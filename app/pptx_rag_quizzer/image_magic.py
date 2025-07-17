import json
from pptx_rag_quizzer.utils import ExtractText_OCR, clean_text


class ImageMagic:

    def __init__(self, rag_controller):
        self.rag_controller = rag_controller

    def describe_image(
        self, image_bytes: bytes, image_format: str = "png", slide_number: str = 0
    ):
        """
        Describes an image using a multi-stage RAG pipeline:
        1. OCR extraction
        2. Enhanced description using OCR + image + slide context
        3. Context retrieval using enhanced description
        4. Final description with context

        Args:
            image_bytes (bytes): The image data
            image_format (str): The image format (png, jpg, etc.)
            slide_number (int): The slide number where the image is located

        Returns:
            str: Enhanced description of the image with context
        """
        # Stage 1: Get OCR description
        ocr_description = clean_text(ExtractText_OCR(image_bytes))

        # Stage 2: Get enhanced description using OCR + image + slide context
        slide_context = self.rag_controller.get_context_from_slide_number(
            int(slide_number)
        )
        enhanced_description = self.get_enhanced_description(
            ocr_description, image_bytes, image_format, slide_context
        )

        # Stage 3: Get context using the enhanced description
        context = self.get_context_from_enhanced_description(enhanced_description)

        # Stage 4: Final description with image + enhanced description + context
        final_description = self.get_final_description(
            enhanced_description, context, image_bytes, image_format
        )

        return final_description

    def get_enhanced_description(
        self,
        ocr_description: str,
        image_bytes: bytes,
        image_format: str,
        slide_context: str,
    ):
        """
        Stage 2: Get enhanced description using OCR + image + slide context.

        Args:
            ocr_description (str): The OCR text from the image
            image_bytes (bytes): The image data
            image_format (str): The image format
            slide_context (str): The slide context

        Returns:
            str: Enhanced description of the image
        """
        # Build the prompt with OCR and slide context
        context_info = ""
        if slide_context:
            context_info = f"\n\nSlide Context:\n{slide_context}"

        prompt = f"""<prompt>
                        <instructions>
                            You are an expert visual analyst providing concise descriptions for a RAG system.
                            Your task is to describe an image from a PowerPoint slide.
                            Describe the image primarily based on its visual content.
                            The description must be 1 to 3 sentences long and focus on the most important visual elements and their core meaning.
                            Incorporate the provided OCR text or slide context only if it directly clarifies or adds significant understanding to the image's visual elements. Do not include context that merely repeats what's obvious in the image or is irrelevant.
                        </instructions>

                        <input_data>
                            <ocr_text>{ocr_description}</ocr_text>
                            <slide_context>{context_info}</slide_context>
                        </input_data>

                        <output_format>
                            Description: description
                        </output_format>

                        <examples>
                            <example>
                            <input>
                                <ocr_text>Quarterly Revenue Trends</ocr_text>
                                <slide_context>This slide details the financial performance over the past year, highlighting growth in emerging markets.</slide_context>
                            </input>
                            <output>
                                Description: A line graph displays fluctuating quarterly revenue trends over a year, with a noticeable upward curve towards the end. The chart, titled "Quarterly Revenue Trends," visually represents the company's financial trajectory, which is further supported by the context of growth in emerging markets.
                            </output>
                            </example>
                        </examples>
                        </prompt>
                """

        clean_prompt = clean_text(prompt)

        enhanced_description = self.rag_controller.prompt_gemini_with_image(
            prompt=clean_prompt,
            image_bytes=image_bytes,
            image_format=image_format,
            max_output_tokens=200,
        )

        return clean_text(enhanced_description)

    def get_context_from_enhanced_description(
        self, enhanced_description: str, n_results: int = 3
    ):
        """
        Stage 3: Get context from the picture collection using enhanced description.

        Args:
            enhanced_description (str): The enhanced description of the image
            n_results (int): Number of most relevant documents to retrieve

        Returns:
            str: Combined context from most relevant slides
        """
        # Query the collection using the enhanced description
        retrieved_results = self.rag_controller.query_collection(
            query_text=enhanced_description,
            collection_name="picture",
            n_results=n_results,
        )

        return retrieved_results

    def get_final_description(
        self,
        enhanced_description: str,
        context: str,
        image_bytes: bytes,
        image_format: str,
    ):
        """
        Stage 4: Get final description with image + enhanced description + context.

        Args:
            enhanced_description (str): The enhanced description from stage 2
            context (str): The retrieved context from stage 3
            image_bytes (bytes): The image data
            image_format (str): The image format

        Returns:
            str: Final enhanced description with context
        """
        prompt = f"""<prompt>
                        <instructions>
                            You are a meticulous content refiner for a RAG system, focused on image descriptions.
                            Your task is to refine a given image description based on newly retrieved contextual information.
                            The refined description must be 1 to 3 sentences long.
                            The primary focus remains the image's visual content. Only incorporate the retrieved context if it provides new, crucial clarity or meaning that is not evident from the current description alone. Do not force context if it doesn't genuinely enhance the visual explanation.
                        </instructions>

                        <input_data>
                            <current_description>{enhanced_description}</current_description>
                            <retrieved_context>{context}</retrieved_context>
                        </input_data>

                        <output_format>
                            Description: description
                        </output_format>

                        <examples>
                            <example>
                            <input>
                                <current_description>A diagram shows interconnected boxes with arrows.</current_description>
                                <retrieved_context>This diagram illustrates the "Customer Journey Map," detailing touchpoints from awareness to loyalty. The slide's title is "Understanding Our Customer Funnel."</retrieved_context>
                            </input>
                            <output>
                                Description: A flowchart diagram depicts a multi-stage process with interconnected boxes and arrows, visually representing a customer journey map. The diagram, aligned with the concept of a customer funnel, illustrates sequential touchpoints from initial awareness through to loyalty.
                            </output>
                            </example>
                        </examples>
                        </prompt>
            """

        clean_prompt = clean_text(prompt)

        final_description = self.rag_controller.prompt_gemini_with_image(
            prompt=clean_prompt,
            image_bytes=image_bytes,
            image_format=image_format,
            max_output_tokens=200,
        )

        return clean_text(final_description)
