from typing import List, Dict, Any
from src.models.models import call_models
import json

def get_generic_model_name(model: str) -> str:
    """Convert specific model names to generic ones (e.g., 'gpt-4' -> 'GPT')"""
    if model.startswith('gpt'):
        return 'GPT'
    elif model.startswith('claude'):
        return 'CLAUDE'
    elif model.startswith('gemini'):
        return 'GEMINI'
    return model.upper()

def format_prompt(input_type: str, prompt: str, prior_results: List[Dict[str, str]] = None) -> str:
    """Format the prompt based on input type and prior results"""
    if input_type == "gsheets":
        return prompt
    elif input_type == "prior_model_output_only" and prior_results:
        # Get the last model's output from the previous result
        last_result = prior_results[-1]
        return next(iter(last_result.values()))  # Get first (and should be only) value
    elif input_type == "prior_all_models_output" and prior_results:
        # Combine all model outputs from the previous result
        last_result = prior_results[-1]
        return "\n".join(f"{model}: {output}" for model, output in last_result.items())
    return prompt

def evaluate_row_debug(
    present: List[Dict[str, str]],
    prompt: str,
    attachments: List[str],
    clients: Dict[str, Any],
) -> List[Dict[str, str]]:
    """
    Debug version of evaluate_row that simulates model calls without making actual API calls.
    Writes test outputs into the dictionary.
    """
    results = []
    for instr_index, instr in enumerate(present):
        print(f"\n📘 Present Row #{instr_index+1}")
        print(f"   Input Type: {instr.get('input', 'gsheets')}")
        print(f"   Active Models: {instr.get('active_models', '')}")

        models = [m.strip() for m in instr.get("active_models", "").split(",") if m.strip()]
        if not models:
            print("   ⚠️ No active models specified")
            continue

        try:
            # Format prompt based on input type
            formatted_prompt = format_prompt(
                instr.get('input', 'gsheets'),
                prompt,
                results  # Pass previous results for prior model outputs
            )
            print(f"   Formatted Prompt: {formatted_prompt}")

            # Simulate model calls
            model_results = {}
            for model in models:
                print(f"\n   🤖 Would call model: {model}")
                print(f"      With prompt: {formatted_prompt}")
                print(f"      With question: {prompt}")
                print(f"      With attachments: {attachments}")
                
                # Simulate a response based on the model and prompt
                generic_name = get_generic_model_name(model)
                simulated_response = f"[DEBUG] {generic_name} response to: {formatted_prompt[:50]}..."
                model_results[model] = simulated_response

            # Convert specific model names to generic ones
            generic_results = {get_generic_model_name(model): output 
                             for model, output in model_results.items()}
            print(f"   📄 Simulated Results: {generic_results}")
            results.append(generic_results)
        except Exception as e:
            print(f"   ❌ Error in debug mode: {e}")
            results.append({get_generic_model_name(model): f"[Error: {e}]" for model in models})

    return results

def evaluate_row(
    present: List[Dict[str, str]],
    prompt: str,
    clients: Dict[str, Any],
) -> List[Dict[str, str]]:
    """
    For each row in the present, evaluates using the specified model(s) with the given prompt,
    and returns a list of dicts mapping generic model name to output.
    Example: [{"CLAUDE": "Output", "GPT": "XYZ"}, {"GEMINI": "XYZ"}]
    """
    results = []
    for instr_index, instr in enumerate(present):
        print(f"\n📘 Present Row #{instr_index+1}")
        print(f"   Input Type: {instr.get('input', 'gsheets')}")
        print(f"   Active Models: {instr.get('active_models', '')}")

        models = [m.strip() for m in instr.get("active_models", "").split(",") if m.strip()]
        if not models:
            print("   ⚠️ No active models specified")
            continue

        try:
            # Format prompt based on input type
            formatted_prompt = format_prompt(
                instr.get('input', 'gsheets'),
                prompt,
                results  # Pass previous results for prior model outputs
            )
            print(f"   Formatted Prompt: {formatted_prompt}")

            # Call each model individually since call_models expects a single model
            model_results = {}
            for model in models:
                response = call_models(
                    clients=clients,
                    model_string=model,
                    prompt=formatted_prompt,
                    question=prompt,  # Original prompt for context
                    files=[],
                )
                model_results[model] = response

            # Convert specific model names to generic ones
            generic_results = {get_generic_model_name(model): output 
                             for model, output in model_results.items()}
            print(f"   📄 Results: {generic_results}")
            results.append(generic_results)
        except Exception as e:
            print(f"   ❌ Error evaluating models: {e}")
            results.append({get_generic_model_name(model): f"[Error: {e}]" for model in models})

    return results

def read_input(
    clients: Dict[str, Any],
    instructions: List[Dict[str, str]],
    input_files: List[str],
) -> List[Dict[str, str]]:
    """Read input files and process them according to instructions."""
    results = []
    for instr_index, instr in enumerate(instructions):
        print(f"\n📘 Present Row #{instr_index+1}")
        print(f"   Input Type: {instr.get('input', 'gsheets')}")
        print(f"   Active Models: {instr.get('active_models', '')}")

        models = [m.strip() for m in instr.get("active_models", "").split(",") if m.strip()]
        if not models:
            print("   ⚠️ No active models specified")
            continue

        try:
            # Format prompt based on input type
            formatted_prompt = format_prompt(
                instr.get('input', 'gsheets'),
                instr.get('prompt', ''),
                results  # Pass previous results for prior model outputs
            )
            print(f"   Formatted Prompt: {formatted_prompt}")

            # Call each model individually
            model_results = {}
            for model in models:
                response = call_models(
                    clients=clients,
                    model_string=model,
                    prompt=formatted_prompt,
                    question=instr.get('prompt', ''),
                    files=input_files,
                    attachments=[]
                )
                model_results[model] = response

            # Convert specific model names to generic ones
            generic_results = {get_generic_model_name(model): output 
                             for model, output in model_results.items()}
            print(f"   📄 Results: {generic_results}")
            results.append(generic_results)
        except Exception as e:
            print(f"   ❌ Error evaluating models: {e}")
            results.append({get_generic_model_name(model): f"[Error: {e}]" for model in models})

    return results

def save_final_output_to_json(results: List[Dict[str, str]], output_path: str = "model_output.json") -> None:
    """Save the final model output to a JSON file.
    
    Args:
        results: List of dictionaries containing model outputs
        output_path: Path where the JSON file should be saved (defaults to 'model_output.json')
    """
    if not results:
        raise ValueError("No results to save")
    
    final_output = results[-1]
    if len(final_output) != 1:
        raise ValueError(f"Expected exactly one model output, got {len(final_output)}")
    
    # Get the single model output
    model_output = next(iter(final_output.values()))
    
    # Handle markdown code blocks
    if model_output.startswith("```json"):
        model_output = model_output.split("```json")[1]
    if model_output.endswith("```"):
        model_output = model_output.rsplit("```", 1)[0]
    model_output = model_output.strip()
    
    try:
        # Try to parse as JSON first to validate
        json.loads(model_output)
        # If valid JSON, write directly
        with open(output_path, 'w') as f:
            f.write(model_output)
    except json.JSONDecodeError:
        # If not valid JSON, wrap in a dict
        with open(output_path, 'w') as f:
            json.dump({"output": model_output}, f, indent=2)
