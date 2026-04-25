# In uhg_gemini.py (inside the UHGChatGemini class we built earlier)
# Update the _generate method to handle stop sequences:

    def _generate(self, messages, stop=None, **kwargs):
        prompt = "\n".join([m.content for m in messages])
        client = self._get_client()
        
        # ADD THIS: Pass stop sequences if LangChain provides them
        config_args = {"temperature": 0.0}
        if stop:
            config_args["stop_sequences"] = stop
            
        response = client.models.generate_content(
            model=self.model_name,
            contents=prompt,
            config=types.GenerateContentConfig(**config_args) # Apply config
        )
        
        message = AIMessage(content=response.text)
        return ChatResult(generations=[ChatGeneration(message=message)])