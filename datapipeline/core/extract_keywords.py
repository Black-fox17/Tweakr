from langchain_google_genai import (
    ChatGoogleGenerativeAI,
    HarmBlockThreshold,
    HarmCategory,
)
from langchain_core.prompts import ChatPromptTemplate
from core.retry_with_backoff import retry_with_backoff



class ExtractKeywords:
    def __init__(self):

        self.llm = ChatGoogleGenerativeAI(
            model="gemini-1.5-pro",
            temperature=0,
            max_tokens=None,
            timeout=None,
            max_retries=2,
            safety_settings={
                HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_NONE,
            },
        )

        self.prompt = ChatPromptTemplate.from_messages(
            [
                (
                    "system",
                    "You are an advanced AI assistant specialized in natural language processing. Your task is to extract all meaningful keywords from the given academic text. Focus on identifying key concepts, topics, and important terms.",
                ),
                ("human", "Here is the academic text:\n\n{text}\n\nPlease provide a list of keywords extracted from this text."),
            ]
        )


    def extract_keywords(self, content: str) -> list:
        """
        Extract keywords from the paper content using ChatGoogleGenerativeAI.
        """
        try:
            def fetch_response():
                chain = self.prompt | self.llm
                return chain.invoke({"text": content})
            
            # Call the fetch_response function with retry logic
            response = retry_with_backoff(fetch_response, max_retries=1, initial_delay=3)
            print("Response: ", response)

            # Check if the response is a dictionary and extract the "content" field
            if isinstance(response, dict) and "content" in response:
                content_text = response["content"]
            else:
                # Attempt to parse the response as a string
                response_str = str(response)
                if "content=" in response_str:
                    content_start = response_str.find("content=\"") + len("content=\"")
                    content_end = response_str.find("\"", content_start)
                    content_text = response_str[content_start:content_end]
                else:
                    raise ValueError("Could not extract 'content' from response.")

            # Process the content text line by line using splitlines()
            content_text = content_text.replace("\\n", "\n")
            keywords = []
            for line in content_text.splitlines():
                # Strip leading '*' or '**', as well as any extra spaces
                cleaned_keyword = line.lstrip("* ").lstrip("**").strip("\n*")
                if cleaned_keyword:  # Skip empty lines
                    keywords.append(cleaned_keyword)
            return keywords

        except Exception as e:
            print(f"Error extracting keywords: {e}")
            return []



# if __name__ == "__main__":
#     extractor = ExtractKeywords(max_retries=3, initial_delay=2)
#     content = "This is some example academic content for testing."
#     keywords = extractor.extract_keywords(content)
#     print("Extracted Keywords: ", keywords)