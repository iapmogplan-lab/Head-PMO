import os
import json
import google.generativeai as genai
import database

# Configure Gemini API key
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

# Initialize Gemini model for function calling
# Using 'gemini-pro' for text-only interactions, 'gemini-pro-vision' for multimodal
model = genai.GenerativeModel(
    model_name="gemini-pro",
    tools=[
        {
            "function_declarations": [
                {
                    "name": "get_current_projects",
                    "description": "Retorna uma lista de todos os projetos existentes.",
                    "parameters": {
                        "type": "object",
                        "properties": {},
                        "required": [],
                    },
                },
                {
                    "name": "get_project_tasks",
                    "description": "Retorna uma lista de tarefas para um projeto específico.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "project_name": {
                                "type": "string",
                                "description": "O nome do projeto.",
                            }
                        },
                        "required": ["project_name"],
                    },
                },
                {
                    "name": "create_project",
                    "description": "Cria um novo projeto com o nome e descrição fornecidos.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "name": {
                                "type": "string",
                                "description": "O nome do projeto.",
                            },
                            "description": {
                                "type": "string",
                                "description": "A descrição do projeto.",
                            },
                        },
                        "required": ["name"],
                    },
                },
                {
                    "name": "create_task",
                    "description": "Cria uma nova tarefa para um projeto específico.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "project_name": {
                                "type": "string",
                                "description": "O nome do projeto ao qual a tarefa pertence.",
                            },
                            "description": {
                                "type": "string",
                                "description": "A descrição da tarefa.",
                            },
                            "status": {
                                "type": "string",
                                "description": "O status inicial da tarefa (ex: A Fazer, Em Andamento, Concluído).",
                            },
                            "due_date": {
                                "type": "string",
                                "description": "A data de vencimento da tarefa (formato YYYY-MM-DD).",
                            },
                            "assigned_to": {
                                "type": "string",
                                "description": "A pessoa atribuída à tarefa.",
                            },
                        },
                        "required": ["project_name", "description"],
                    },
                },
                {
                    "name": "update_task_status",
                    "description": "Atualiza o status de uma tarefa existente.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "task_id": {
                                "type": "integer",
                                "description": "O ID da tarefa a ser atualizada.",
                            },
                            "status": {
                                "type": "string",
                                "description": "O novo status da tarefa (ex: A Fazer, Em Andamento, Concluído).",
                            },
                        },
                        "required": ["task_id", "status"],
                    },
                },
                {
                    "name": "delete_task_by_id",
                    "description": "Deleta uma tarefa pelo seu ID.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "task_id": {
                                "type": "integer",
                                "description": "O ID da tarefa a ser deletada.",
                            }
                        },
                        "required": ["task_id"],
                    },
                },
                {
                    "name": "delete_project_by_id",
                    "description": "Deleta um projeto pelo seu ID e todas as suas tarefas associadas.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "project_id": {
                                "type": "integer",
                                "description": "O ID do projeto a ser deletado.",
                            }
                        },
                        "required": ["project_id"],
                    },
                },
            ]
        }
    ]
)

# Define available tools for the agent
available_tools = {
    "get_current_projects": database.get_projects,
    "get_project_tasks": database.get_tasks,
    "create_project": database.add_project,
    "create_task": database.add_task,
    "update_task_status": database.update_task,
    "delete_task_by_id": database.delete_task,
    "delete_project_by_id": database.delete_project,
}

def run_conversation(user_message, chat_history):
    # Start a new chat session if history is empty
    if not chat_history:
        chat = model.start_chat(history=[])
    else:
        # Gemini expects history in a specific format
        gemini_history = []
        for msg in chat_history:
            if msg["role"] == "user":
                gemini_history.append(genai.types.GenerationConfig(role="user", parts=[msg["content"]]))
            elif msg["role"] == "assistant":
                # Assistant messages can be text or tool calls
                if "tool_calls" in msg:
                    tool_calls_parts = []
                    for tc in msg["tool_calls"]:
                        tool_calls_parts.append(genai.types.GenerationConfig(function_call=genai.types.FunctionCall(name=tc["function"]["name"], args=tc["function"]["arguments"]))) # Assuming arguments are already a dict
                    gemini_history.append(genai.types.GenerationConfig(role="model", parts=tool_calls_parts))
                else:
                    gemini_history.append(genai.types.GenerationConfig(role="model", parts=[msg["content"]]))
            elif msg["role"] == "tool":
                # Tool messages are responses to function calls
                gemini_history.append(genai.types.GenerationConfig(role="function", name=msg["name"], parts=[msg["content"]]))

        chat = model.start_chat(history=gemini_history)

    response = chat.send_message(user_message)

    # Process potential function calls
    if response.candidates and response.candidates[0].content.parts:
        for part in response.candidates[0].content.parts:
            if part.function_call:
                function_call = part.function_call
                function_name = function_call.name
                function_args = {k: v for k, v in function_call.args.items()}

                if function_name in available_tools:
                    # Special handling for database functions that return raw data
                    if function_name in ["get_current_projects", "get_project_tasks"]:
                        result = available_tools[function_name](**function_args)
                        # Convert list of dicts to a more readable string for the model
                        if isinstance(result, list):
                            formatted_result = json.dumps(result, indent=2)
                        else:
                            formatted_result = json.dumps(result)
                    elif function_name == "create_task":
                        # The database.add_task expects project_id, not project_name
                        project_name = function_args.pop("project_name")
                        project = database.get_project_by_name(project_name)
                        if project:
                            function_args["project_id"] = project["id"]
                            result = available_tools[function_name](**function_args)
                            result = {"message": f"Tarefa criada com sucesso! ID: {result}"}
                        else:
                            result = {"error": f"Projeto '{project_name}' não encontrado."}
                        formatted_result = json.dumps(result)
                    elif function_name == "create_project":
                        result = available_tools[function_name](**function_args)
                        if result:
                            formatted_result = json.dumps({"message": f"Projeto criado com sucesso! ID: {result}"})
                        else:
                            formatted_result = json.dumps({"error": f"Projeto '{function_args['name']}' já existe ou houve um erro."})
                    elif function_name == "update_task_status":
                        result = available_tools[function_name](**function_args)
                        if result:
                            formatted_result = json.dumps({"message": f"Status da tarefa {function_args['task_id']} atualizado para '{function_args['status']}'."})
                        else:
                            formatted_result = json.dumps({"error": f"Tarefa {function_args['task_id']} não encontrada ou erro ao atualizar."})
                    elif function_name == "delete_task_by_id":
                        result = available_tools[function_name](**function_args)
                        if result:
                            formatted_result = json.dumps({"message": f"Tarefa {function_args['task_id']} deletada com sucesso."})
                        else:
                            formatted_result = json.dumps({"error": f"Tarefa {function_args['task_id']} não encontrada ou erro ao deletar."})
                    elif function_name == "delete_project_by_id":
                        result = available_tools[function_name](**function_args)
                        if result:
                            formatted_result = json.dumps({"message": f"Projeto {function_args['project_id']} e suas tarefas deletados com sucesso."})
                        else:
                            formatted_result = json.dumps({"error": f"Projeto {function_args['project_id']} não encontrado ou erro ao deletar."})
                    else:
                        result = available_tools[function_name](**function_args)
                        formatted_result = json.dumps(result)

                    # Add tool call and its result to history
                    chat_history.append({
                        "role": "assistant",
                        "tool_calls": [{
                            "function": {
                                "name": function_name,
                                "arguments": function_args
                            }
                        }]
                    })
                    chat_history.append({"role": "tool", "name": function_name, "content": formatted_result})

                    # Get the final response from the model after tool execution
                    final_response = chat.send_message(genai.types.GenerationConfig(role="function", name=function_name, parts=[formatted_result]))
                    return final_response.text, chat_history
                else:
                    return f"Erro: Função desconhecida '{function_name}'.", chat_history

    return response.text, chat_history
