from html import entities
from typing import Dict, Text, Any, List

from rasa.engine.graph import GraphComponent, ExecutionContext
from rasa.engine.recipes.default_recipe import DefaultV1Recipe
from rasa.engine.storage.resource import Resource
from rasa.engine.storage.storage import ModelStorage
from rasa.shared.nlu.training_data.message import Message

import recognizers_suite as Recognizers
from recognizers_suite import Culture, ModelResult


@DefaultV1Recipe.register(
    DefaultV1Recipe.ComponentType.ENTITY_EXTRACTOR, is_trainable=False
)
class MSTextRecognizer(GraphComponent):
    """Searches for structured entities, e.g. dates, time, email, phonenumber  using a Microsoft.Recognizers.Text."""

    @staticmethod
    def get_default_config() -> Dict[Text, Any]:
        """The component's default config."""
        return {}

    def __init__(self, config: Dict[Text, Any]) -> None:
        """Creates the extractor.
        Args:
            config: The extractor's config.
        """
        self.component_config = config

    @classmethod
    def create(
        cls,
        config: Dict[Text, Any],
        model_storage: ModelStorage,
        resource: Resource,
        execution_context: ExecutionContext,
    ) -> GraphComponent:
        """Creates component (see parent class for full docstring)."""
        return cls(config)

    @staticmethod
    def parse_all(user_input: str, culture: str) -> List[List[ModelResult]]:
        """
        extracts all entity types for the given user input
        """
        return [
            # Number recognizer - This function will find any number from the input
            # E.g "I have two apples" will return "2".
            Recognizers.recognize_number(user_input, culture),

            # Ordinal number recognizer - This function will find any ordinal number
            # E.g "eleventh" will return "11".
            Recognizers.recognize_ordinal(user_input, culture),

            # Percentage recognizer - This function will find any number presented as percentage
            # E.g "one hundred percents" will return "100%"
            Recognizers.recognize_percentage(user_input, culture),

            # Age recognizer - This function will find any age number presented
            # E.g "After ninety five years of age, perspectives change" will return
            # "95 Year"
            Recognizers.recognize_age(user_input, culture),

            # Currency recognizer - This function will find any currency presented
            # E.g "Interest expense in the 1988 third quarter was $ 75.3 million"
            # will return "75300000 Dollar"
            Recognizers.recognize_currency(user_input, culture),

            # Dimension recognizer - This function will find any dimension presented E.g "The six-mile trip to my airport
            # hotel that had taken 20 minutes earlier in the day took more than
            # three hours." will return "6 Mile"
            Recognizers.recognize_dimension(user_input, culture),

            # Temperature recognizer - This function will find any temperature presented
            # E.g "Set the temperature to 30 degrees celsius" will return "30 C"
            Recognizers.recognize_temperature(user_input, culture),

            # DateTime recognizer - This function will find any Date even if its write in colloquial language -
            # E.g "I'll go back 8pm today" will return "2017-10-04 20:00:00"
            Recognizers.recognize_datetime(user_input, culture),

            # PhoneNumber recognizer will find any phone number presented
            # E.g "My phone number is ( 19 ) 38294427."
            Recognizers.recognize_phone_number(user_input, culture),

            # Email recognizer will find any phone number presented
            # E.g "Please write to me at Dave@abc.com for more information on task
            # #A1"
            Recognizers.recognize_email(user_input, culture),
        ]


    @staticmethod
    def convert_to_rasa(value: str, type: str) -> Dict[Text, Any]:
        """Convert prediction output into the Rasa NLU compatible output format."""
        entity = {
            "value": value,
            "confidence": "1.0",
            "entity": type,
            "extractor": "ms_text_recognizer",
        }
        return entity

    def process(self, messages: List[Message]) -> List[Message]:
        """Retrieve the text message, pass it to the parser
            and append the prediction results to the message class."""
        for message in messages:
            results = self.parse_all(message.get("text"), Culture.English)
            results = [item for sublist in results for item in sublist]
            entities = []
            for result in results:
                # entity_type = result.resolution["values"][0]['type']
                resolution = result.resolution
                if "value" in resolution:
                    entity_type = result.type_name
                    entity_value = result.resolution["value"]
                else:
                    entity_type = result.resolution["values"][0]["type"]
                    entity_value = result.resolution["values"][-1]["value"]

                entity = self.convert_to_rasa(entity_value, entity_type)
                entities.append(entity)
            message.set("entities", entities, add_to_output=True)
        return messages
