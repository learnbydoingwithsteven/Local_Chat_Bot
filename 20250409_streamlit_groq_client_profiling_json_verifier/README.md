# streamlit_groq_client_app.py

import streamlit as st
import json
from groq import Groq, GroqError
import os
import traceback # For detailed error logging

# --- CrewAI Imports ---
from crewai import Agent, Task, Crew, Process
from langchain_groq import ChatGroq # To use Groq with CrewAI via Langchain

# --- Optional: Load .env file if present ---
# try:
#     from dotenv import load_dotenv
#     load_dotenv()
# except ImportError:
#     # dotenv not installed, proceed without it
#     pass

# --- Configuration ---
AVAILABLE_MODELS = [
    "llama3-8b-8192",
    "llama3-70b-8192",
    "mixtral-8x7b-32768",
    "gemma-7b-it",
    "gemma2-9b-it", # Check Groq console for availability
]

TARGET_JSON_STRUCTURE_GUIDE = """
{
  "client_profile": {
    "name": "string",
    "age": "integer",
    "interests": ["list", "of", "strings"],
    "learning_goals": "string (detailed description)",
    "preferred_format": "string (e.g., 'Video', 'Text', 'Interactive', 'Mixed')"
  },
  "metadata": {
    "source_simulation": "string (e.g., 'Simulation 1', 'Simulation 2', 'Simulation 3 - CrewAI')"
  }
}
"""

# --- Helper Functions ---

def get_groq_client(api_key):
    """Initializes and returns a Groq client (for direct calls)."""
    if not api_key:
        st.error("Groq API key is missing.")
        return None
    try:
        client = Groq(api_key=api_key)
        return client
    except GroqError as e:
        st.error(f"Failed to initialize Groq client: {e}")
        return None
    except Exception as e:
        st.error(f"An unexpected error occurred during Groq client initialization: {e}")
        return None

def call_groq_chat(client, model, messages, max_retries=2):
    """Calls the Groq Chat API directly (used in Sim 2)."""
    if not client:
        return None, "Groq client not initialized."

    attempt = 0
    while attempt <= max_retries:
        try:
            chat_completion = client.chat.completions.create(
                messages=messages,
                model=model,
                temperature=0.2,
                max_tokens=1024,
            )
            return chat_completion.choices[0].message.content, None
        except GroqError as e:
            error_message = f"Groq API Error (Attempt {attempt+1}/{max_retries+1}): {e}"
            st.warning(error_message)
            attempt += 1
        except Exception as e:
             error_message = f"An unexpected error occurred during API call (Attempt {attempt+1}/{max_retries+1}): {e}"
             st.warning(error_message)
             attempt += 1
        if attempt > max_retries:
            return None, error_message # Return error after max retries
    return None, "Max retries exceeded without success." # Should only be reached if max_retries < 0


def parse_interests(interests_str):
    """Parses a comma-separated string into a list of interests."""
    if not interests_str:
        return []
    return [interest.strip() for interest in interests_str.split(',') if interest.strip()]

# --- Streamlit App UI ---

st.set_page_config(layout="wide", page_title="Groq Client Profiling")
st.title("Groq Client Profiling Simulations")
st.markdown("Use Groq LLMs to generate client profiles in JSON format for educational product assignment.")

# --- Sidebar for Configuration ---
with st.sidebar:
    st.header("⚙️ Configuration")

    # API Key Input - Store in session state
    if 'groq_api_key' not in st.session_state:
        st.session_state.groq_api_key = os.environ.get("GROQ_API_KEY", "")

    api_key_input = st.text_input(
        "Enter Groq API Key",
        type="password",
        value=st.session_state.groq_api_key,
        help="Get your API key from console.groq.com. Can also be set via GROQ_API_KEY env var.",
    )
    # Update session state and rerun if input changes to ensure components re-initialize if needed
    if api_key_input != st.session_state.groq_api_key:
        st.session_state.groq_api_key = api_key_input
        # Clear dependent state if key changes
        if 'direct_client_initialized' in st.session_state:
            del st.session_state.direct_client_initialized
        st.rerun()

    selected_model = st.selectbox(
        "Choose Groq Model",
        options=AVAILABLE_MODELS,
        index=AVAILABLE_MODELS.index("llama3-8b-8192") if "llama3-8b-8192" in AVAILABLE_MODELS else 0
    )

    st.subheader("Target JSON Structure")
    st.code(TARGET_JSON_STRUCTURE_GUIDE, language="json")

# --- Initialize Direct Groq Client (for Sim 2) ---
# This client uses the API key directly from session state
groq_api_key = st.session_state.get('groq_api_key')
direct_groq_client = None

if not groq_api_key:
    st.warning("Please enter your Groq API Key in the sidebar to begin.")
    st.stop()
else:
    # Use a flag in session state to avoid re-initializing unless the key changed (handled by rerun)
    if 'direct_client_initialized' not in st.session_state or not st.session_state.direct_client_initialized:
        st.session_state.direct_groq_client = get_groq_client(groq_api_key) # Store client in state
        st.session_state.direct_client_initialized = (st.session_state.direct_groq_client is not None)

    direct_groq_client = st.session_state.get('direct_groq_client') # Retrieve from state

    if direct_groq_client:
        st.success("Direct Groq client initialized (for Sim 2).")
    else:
        # Error message was shown by get_groq_client
        st.info("Direct Groq client initialization failed. Simulation 2 might not work.")
        # Don't stop the whole app if only direct client fails

# --- Main Area for Client Info and Simulations ---
st.header("👤 Client Information Input")
col1, col2 = st.columns(2)
with col1:
    client_name = st.text_input("Client Name", "Alex Johnson")
    client_age = st.number_input("Client Age", min_value=0, max_value=120, value=28, step=1)
    client_preferred_format = st.selectbox(
        "Preferred Learning Format",
        ["Video", "Text", "Interactive", "Audio", "Mixed", "Unspecified"],
        index=4
    )
with col2:
    client_interests_raw = st.text_area("Client Interests (comma-separated)", "Cloud Computing, DevOps, Kubernetes, Serverless Architecture")
    client_learning_goals = st.text_area("Client Learning Goals", "Achieve AWS Certified Solutions Architect - Associate certification, learn Infrastructure as Code (Terraform), automate deployment pipelines.")

client_interests_list = parse_interests(client_interests_raw)
st.divider()

# --- Simulation Tabs ---
tab1, tab2, tab3 = st.tabs(["Simulation 1: Manual JSON", "Simulation 2: LLM Formatting", "Simulation 3: CrewAI Agents"])

# --- Simulation 1 (Manual JSON) ---
with tab1:
    st.subheader("Simulation 1: Manual JSON Formulation")
    st.markdown("Directly constructs the JSON based on the input fields and a predefined structure.")
    if st.button("Run Simulation 1", key="sim1_button"):
        st.info("Generating JSON manually...")
        try:
            output_dict = {
                "client_profile": {
                    "name": client_name,
                    "age": int(client_age),
                    "interests": client_interests_list,
                    "learning_goals": client_learning_goals,
                    "preferred_format": client_preferred_format
                },
                "metadata": {
                    "source_simulation": "Simulation 1: Manual JSON"
                }
            }
            st.success("Manual JSON generated successfully:")
            st.json(output_dict)
        except Exception as e:
            st.error(f"Error during manual JSON creation: {e}")


# --- Simulation 2 (LLM Formatting - uses direct_groq_client) ---
with tab2:
    st.subheader("Simulation 2: LLM JSON Formulation")
    st.markdown(f"Sends client information directly to the `{selected_model}` model via `groq-python`.")
    if st.button("Run Simulation 2", key="sim2_button"):
        # Check if direct client is available
        if not direct_groq_client:
             st.error("Direct Groq Client is not available (check API key). Cannot run Simulation 2.")
             st.stop()

        st.info(f"Running Simulation 2 with model: `{selected_model}`...")
        input_text = f"Client Name: {client_name}\nClient Age: {client_age}\nClient Interests: {client_interests_raw}\nClient Learning Goals: {client_learning_goals}\nPreferred Learning Format: {client_preferred_format}"
        messages = [
             {
                "role": "system",
                "content": f"You are a precise data formatting assistant. Convert the provided client details into a JSON object adhering strictly to the following structure. Output ONLY the raw JSON object, without any markdown formatting, comments, or introductory/concluding sentences.\n\nRequired JSON Structure:\n```json\n{TARGET_JSON_STRUCTURE_GUIDE}\n```\nEnsure 'interests' is a JSON list of strings derived from the comma-separated input. Ensure 'age' is a JSON number."
             },
             {
                "role": "user",
                "content": f"Format the following client information into the specified JSON structure:\n\n{input_text}"
             }
        ]

        with st.spinner(f"Asking `{selected_model}` (direct call) to format JSON..."):
            llm_response, error = call_groq_chat(direct_groq_client, selected_model, messages)

        if error:
            st.error(f"Simulation 2 Failed: {error}")
        elif llm_response:
            st.text_area("Raw LLM Response:", llm_response, height=150)
            st.divider()
            # Attempt to parse the LLM response as JSON
            try:
                # More robust cleaning: find first '{' and last '}'
                json_start = llm_response.find('{')
                json_end = llm_response.rfind('}')
                if json_start != -1 and json_end != -1 and json_end >= json_start:
                    json_string = llm_response[json_start:json_end+1].strip()
                else:
                     raise json.JSONDecodeError("No JSON object found in the response.", llm_response, 0)

                parsed_json = json.loads(json_string)

                # Add/update metadata
                if "metadata" not in parsed_json:
                     parsed_json["metadata"] = {}
                parsed_json["metadata"]["source_simulation"] = "Simulation 2: LLM Formatting"
                parsed_json["metadata"]["model_used"] = selected_model

                st.success("LLM response successfully parsed as JSON:")
                st.json(parsed_json)
            except json.JSONDecodeError as e:
                st.error(f"Failed to parse LLM response as JSON: {e}")
                st.warning("The LLM did not return a valid JSON object.")
            except Exception as e:
                 st.error(f"An unexpected error occurred during JSON parsing: {e}")
        else:
            st.error("Simulation 2 Failed: No response received from LLM after retries.")


# --- Simulation 3 (CrewAI Agents - Updated with Temp Env Var & CrewOutput Handling) ---
with tab3:
    st.subheader("Simulation 3: CrewAI Agent Collaboration")
    st.markdown(f"""
    Uses `crewai` to simulate two agents collaborating using `{selected_model}`.
    *(Temporarily sets GROQ_API_KEY environment variable for compatibility with underlying libraries)*
    """)

    if st.button("Run Simulation 3 with CrewAI", key="sim3_crewai_button"):
        current_api_key = st.session_state.get('groq_api_key')
        if not current_api_key:
            st.error("Groq API Key is missing. Cannot run CrewAI simulation.")
            st.stop()

        # --- Temporarily set Environment Variable for LiteLLM ---
        original_env_key = os.environ.get("GROQ_API_KEY") # Store original value (if any)
        os.environ["GROQ_API_KEY"] = current_api_key      # Set it from session state
        st.info("Temporarily set GROQ_API_KEY environment variable for CrewAI run.")
        # --- End Env Var Setting ---

        crew_llm = None # Define crew_llm before try block to ensure it's in scope for finally
        try:
            # Initialize LLM - Let ChatGroq pick up the env var
            # Use the prefixed model name to tell LiteLLM it's Groq
            litellm_model_name = f"groq/{selected_model}"
            st.info(f"Initializing CrewAI LLM with prefixed model: {litellm_model_name} (using env var for API key)")

            crew_llm = ChatGroq(
                temperature=0.2,
                # groq_api_key parameter is omitted here; ChatGroq should use the env var
                model_name=litellm_model_name
            )
            if not crew_llm:
                raise ValueError("ChatGroq object creation failed")
            st.success("CrewAI LLM (ChatGroq) initialized.")

            # --- Define Agents ---
            st.info(f"Defining CrewAI Agents with model: `{selected_model}`...")
            formatter_agent = Agent(
                role='Client Data JSON Formatter',
                goal='Accurately convert provided client details into a JSON object following the specified structure. Output ONLY the raw JSON object.',
                backstory='An expert in data structuring and transformation, focused on precision and adherence to schemas. You meticulously parse details and format them correctly.',
                llm=crew_llm, # Pass the initialized LLM instance
                verbose=False,
                allow_delegation=False,
                max_iter=3 # Limit iterations to prevent excessive loops
            )

            validator_agent = Agent(
                role='JSON Structure and Content Validator',
                goal='Verify that the provided text string is a valid JSON object and strictly conforms to the required schema. Check for correct data types (name=string, age=integer, interests=list of strings, etc.).',
                backstory='A quality assurance specialist focused on data integrity. You double-check every field and the overall structure against the requirements. If valid, output the JSON. If invalid, state the specific reason for failure.',
                llm=crew_llm, # Pass the same LLM instance
                verbose=False,
                allow_delegation=False,
                max_iter=3 # Limit iterations
            )

            # --- Define Tasks ---
            st.info("Defining CrewAI Tasks...")
            client_data_input = f"Name: {client_name}\nAge: {client_age}\nInterests: {client_interests_raw}\nGoals: {client_learning_goals}\nFormat: {client_preferred_format}"

            format_task = Task(
                description=(
                    f'Parse the following client details and format them into a JSON object.\n'
                    f'Client Details:\n---\n{client_data_input}\n---\n'
                    f'Required JSON Structure:\n```json\n{TARGET_JSON_STRUCTURE_GUIDE}\n```\n'
                    f'Pay close attention to data types: age must be an integer, interests must be a list of strings. '
                    f'Output ONLY the raw JSON object without any introduction, explanation, or markdown backticks.'
                ),
                expected_output='A raw string containing ONLY the valid JSON object conforming to the specified structure.',
                agent=formatter_agent
            )

            validate_task = Task(
                description=(
                    f'Receive a string potentially containing a JSON object from the Formatter Agent. '
                    f'Validate two things:\n'
                    f'1. Is the string a syntactically correct JSON object?\n'
                    f'2. Does the JSON object strictly adhere to this required structure and data types?\n'
                    f'Required JSON Structure:\n```json\n{TARGET_JSON_STRUCTURE_GUIDE}\n```\n'
                    f'If BOTH conditions are met, output the validated raw JSON string. '
                    f'If EITHER condition fails, output a concise error message explaining exactly what is wrong (e.g., "Invalid JSON syntax", "Missing field: age", "Incorrect type for interests: expected list"). Do NOT output the invalid JSON.'
                ),
                expected_output='Either the validated raw JSON string (if valid) or a specific error message string (if invalid).',
                agent=validator_agent
            )

            # --- Define and Run Crew ---
            st.info("Setting up and running CrewAI...")
            client_profiling_crew = Crew(
                agents=[formatter_agent, validator_agent],
                tasks=[format_task, validate_task],
                process=Process.sequential, # Run tasks one after the other
                verbose=0 # Set to 1 or 2 for console debugging if needed
            )

            st.markdown("**CrewAI Agents Working...**")
            with st.spinner("Formatter Agent is processing... -> Validator Agent is checking..."):
                # Kickoff the crew and get the result from the *last* task (validation)
                crew_result = client_profiling_crew.kickoff() # This returns a CrewOutput object

            # --- Process Results ---
            st.divider()
            st.markdown("**CrewAI Final Output (Result from Validator Agent):**")
            # --- MODIFICATION: Display the .raw attribute ---
            # Access the raw string output from the CrewOutput object
            # Add fallback to str() in case .raw doesn't exist for some reason
            raw_output_string = crew_result.raw if hasattr(crew_result, 'raw') else str(crew_result)
            st.text_area("Raw Output from Crew:", raw_output_string, height=150)
            # --- END MODIFICATION ---


            # --- Post-CrewAI Validation (using Python) ---
            st.divider()
            st.markdown("**Final Validation (Python `json.loads`)**")
            validated_json = None
            validation_error_msg = None
            try:
                # --- MODIFICATION: Use raw_output_string ---
                # Add a check if raw_output_string is actually a string
                if not isinstance(raw_output_string, str):
                    validation_error_msg = f"CrewAI output's .raw attribute is not a string (Type: {type(raw_output_string)}). Cannot perform JSON validation."
                    st.error(validation_error_msg)
                    # Optionally display the non-string output:
                    # st.write("Non-string raw output:", raw_output_string)
                else:
                    # Basic cleaning: find first '{' and last '}' on the raw string
                    json_start = raw_output_string.find('{')
                    json_end = raw_output_string.rfind('}')

                    if json_start != -1 and json_end != -1 and json_end >= json_start:
                        # Use the raw_output_string for slicing
                        json_string = raw_output_string[json_start:json_end+1].strip()
                        # Attempt parsing
                        validated_json = json.loads(json_string)

                        # Add/update metadata after successful validation
                        if "metadata" not in validated_json:
                            validated_json["metadata"] = {}
                        validated_json["metadata"]["source_simulation"] = "Simulation 3: CrewAI Agents"
                        validated_json["metadata"]["model_used"] = selected_model # Store the base model name

                        st.success("✅ Final validation successful! The output is valid JSON.")
                        st.json(validated_json)

                    else:
                        # If the crew result doesn't look like JSON, it might be an error message from the validator agent
                        validation_error_msg = "CrewAI output does not contain a recognizable JSON object. It might be an error message from the Validator Agent."
                        st.warning(validation_error_msg)
                        st.info("Review the 'Raw Output from Crew' above to see the Validator Agent's response.")
                # --- END MODIFICATION ---

            except json.JSONDecodeError as e:
                # --- MODIFICATION: Ensure raw_output_string is used in error message context if needed ---
                # Show only the beginning of the potentially long string in the error
                raw_output_snippet = raw_output_string[:100] + "..." if isinstance(raw_output_string, str) else str(raw_output_string)
                validation_error_msg = f"Final Validation Failed! The CrewAI output ('{raw_output_snippet}') is not valid JSON. Error: {e}"
                st.error(validation_error_msg)
                st.warning("This could mean the Formatter Agent failed, the Validator Agent failed to catch the error, or the Validator Agent correctly identified an error but didn't output valid JSON itself (as instructed).")
                st.info("Review the 'Raw Output from Crew' above.")
            except Exception as e:
                validation_error_msg = f"An unexpected error occurred during final validation: {e}"
                st.error(validation_error_msg)

        except Exception as e:
            st.error(f"An error occurred during CrewAI setup or execution: {e}")
            st.error("Traceback:")
            st.code(traceback.format_exc()) # Keep showing traceback for debugging

        finally:
            # --- Restore Environment Variable ---
            st.info("Restoring original GROQ_API_KEY environment variable state.")
            if original_env_key is None:
                # If it wasn't set before, remove it entirely
                if "GROQ_API_KEY" in os.environ:
                    del os.environ["GROQ_API_KEY"]
            else:
                # If it was set before, restore its original value
                os.environ["GROQ_API_KEY"] = original_env_key
            # --- End Env Var Restoration ---
