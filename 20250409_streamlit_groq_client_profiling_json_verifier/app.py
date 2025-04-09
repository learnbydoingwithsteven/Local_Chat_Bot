# Find this section in Simulation 3 (around line 375 in the previous code)

            # --- Process Results ---
            st.divider()
            st.markdown("**CrewAI Final Output (Result from Validator Agent):**")
            # --- MODIFICATION: Display the .raw attribute ---
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
                validation_error_msg = f"Final Validation Failed! The CrewAI output ('{raw_output_string[:100]}...') is not valid JSON. Error: {e}"
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
            # --- Restore Environment Variable (Code unchanged here) ---
            st.info("Restoring original GROQ_API_KEY environment variable state.")
            if original_env_key is None:
                if "GROQ_API_KEY" in os.environ:
                    del os.environ["GROQ_API_KEY"]
            else:
                os.environ["GROQ_API_KEY"] = original_env_key
            # --- End Env Var Restoration ---
