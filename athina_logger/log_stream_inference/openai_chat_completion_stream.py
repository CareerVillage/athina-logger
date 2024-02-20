from typing import List, Optional, Dict, Any
import tiktoken
from ..constants import LOG_INFERENCE_URL
from .log_stream_inference import LogStreamInference
from ..api_key import AthinaApiKey
from ..request_helper import RequestHelper
from ..util.token_count_helper import get_prompt_tokens_openai_chat_completion, get_completion_tokens_openai_chat_completion


class LogOpenAiChatCompletionStreamInference(LogStreamInference, AthinaApiKey):
    def __init__(self,
                 prompt_slug: str,
                 prompt: List[Dict[str, Any]],
                 language_model_id: str,
                 response_time: Optional[int] = None,
                 context: Optional[Dict] = None,
                 environment: Optional[str] = 'production',
                 customer_id: Optional[str] = None,
                 customer_user_id: Optional[str] = None,
                 session_id: Optional[str] = None,
                 user_query: Optional[str] = None,
                 external_reference_id: Optional[str] = None,
                 custom_attributes: Optional[Dict] = None):
        """
        constructor for log stream inference
        :param prompt_slug: str - The slug of the prompt used for the inference.
        :param prompt: List[Dict[str, Any]] - The messages used for the inference.
        :param language_model_id: str - The model used for the inference.
        :param response_time: Optional[int] - The response time in milliseconds. Defaults to None.
        :param context: Optional[Dict] - A dictionary containing additional context information. Defaults to None.
        :param environment: Optional[str] - The environment in which the inference occurred. Defaults to production.
        :param customer_id: Optional[str] - The customer's unique identifier. Defaults to None.
        :param customer_user_id: Optional[str] - The customer's user identifier. Defaults to None.
        :param session_id: Optional[str] - The session identifier. Defaults to None.
        :param user_query: Optional[str] - The user's query or input. Defaults to None.
        :param external_reference_id: Optional[str] - The external reference id. Defaults to None.
        :param custom_attributes: Optional[Dict] - A dictionary containing custom attributes. Defaults to None.
        """
        super().__init__(
            prompt_slug=prompt_slug,
            response_time=response_time,
            context=context,
            environment=environment,
            customer_id=customer_id,
            customer_user_id=customer_user_id,
            session_id=session_id,
            user_query=user_query,
            external_reference_id=external_reference_id,
            custom_attributes=custom_attributes)
        self.prompt = prompt
        self.language_model_id = language_model_id
        self.response = ''

    def _get_text_from_stream_chunk(self, stream_chunk):
        """
        gets the text from the stream chunk
        """
        try:
            text = ''
            choices = stream_chunk.get('choices', []) 
            if choices and len(choices) > 0 and 'delta' in choices[0]:
                delta = choices[0].get('delta', {})
                if 'content' in delta and delta['content'] is not None:
                    text = delta.get('content', '')

            return text
        except Exception as e:
            raise e

    def collect_stream_inference(self, response):
        """
        collects the inference from the log stream
        """
        try:
            for stream_chunk in response:
                if isinstance(stream_chunk, dict):
                    self.response += self._get_text_from_stream_chunk(
                        stream_chunk)
                else:
                    self.response += self._get_text_from_stream_chunk(
                        stream_chunk.model_dump())
        except Exception as e:
            raise e

    def collect_stream_inference_by_chunk(self, stream_chunk):
        """
        collects the inference from the log stream of openai chat completion chunk by chunk
        """
        try:
            if isinstance(stream_chunk, dict):
                self.response += self._get_text_from_stream_chunk(
                    stream_chunk)
            else:
                self.response += self._get_text_from_stream_chunk(
                    stream_chunk.model_dump())
        except Exception as e:
            raise e

    def log_stream_inference(self):
        """
        logs the stream inference to the athina api server
        """
        try:
            prompt_tokens = self._get_prompt_tokens(
                prompt=self.prompt, language_model_id=self.language_model_id)

            completion_tokens = self._get_completion_tokens(
                response=self.response, language_model_id=self.language_model_id)

            if prompt_tokens is not None and completion_tokens is not None:
                total_tokens = prompt_tokens + completion_tokens
            else:
                total_tokens = None
            payload = {
                'prompt_slug': self.prompt_slug,
                'prompt': self.prompt,
                'language_model_id': self.language_model_id,
                'response': self.response,
                'response_time': self.response_time,
                'context': self.context,
                'environment': self.environment,
                'customer_id': str(self.customer_id) if self.customer_id is not None else None,
                'customer_user_id': str(self.customer_user_id) if self.customer_user_id is not None else None,
                'session_id': str(self.session_id) if self.session_id is not None else None,
                'user_query': str(self.user_query) if self.user_query is not None else None,
                'external_reference_id': str(self.external_reference_id) if self.external_reference_id is not None else None,
                'prompt_tokens': prompt_tokens,
                'completion_tokens': completion_tokens,
                'total_tokens': total_tokens,
                'custom_attributes': self.custom_attributes,
            }
            # Remove None fields from the payload
            payload = {k: v for k, v in payload.items() if v is not None}
            RequestHelper.make_post_request(endpoint=LOG_INFERENCE_URL, payload=payload, headers={
                'athina-api-key': LogOpenAiChatCompletionStreamInference.get_api_key(),
            })
        except Exception as e:
            raise e

    def _get_prompt_tokens(self, prompt: List[Dict[str, Any]], language_model_id: str):
        """
        gets the prompt tokens given the prompt for the openai chat model completion
        """
        try:
            tokens = get_prompt_tokens_openai_chat_completion(
                prompt=prompt, language_model_id=language_model_id)
            return tokens
        except Exception as e:
            return None

    def _get_completion_tokens(self, response: str, language_model_id: str):
        """
        gets the completion tokens given the prompt response from the openai chat model completion
        """
        try:
            tokens = get_completion_tokens_openai_chat_completion(
                response=response, language_model_id=language_model_id)
            return tokens
        except Exception as e:
            return None
