import torch
from PIL import Image
from transformers import AutoProcessor, LlavaForConditionalGeneration
import sys

MODEL_NAME = "fancyfeast/llama-joycaption-alpha-two-hf-llava"

# Load JoyCaption
# bfloat16 is the native dtype of the LLM used in JoyCaption (Llama 3.1)
# device_map=0 loads the model into the first GPU
processor = AutoProcessor.from_pretrained(MODEL_NAME)
llava_model = LlavaForConditionalGeneration.from_pretrained(
    MODEL_NAME, torch_dtype="bfloat16", device_map="auto"
)
llava_model.eval()


def chat(convo, image):

    # Format the conversation
    # WARNING: HF's handling of chat's on Llava models is very fragile.  This specific combination of processor.apply_chat_template(), and processor() works
    # but if using other combinations always inspect the final input_ids to ensure they are correct.  Often times you will end up with multiple <bos> tokens
    # if not careful, which can make the model perform poorly.
    convo_string = processor.apply_chat_template(
        convo, tokenize=False, add_generation_prompt=True
    )
    assert isinstance(convo_string, str)

    # Process the inputs
    inputs = processor(text=[convo_string], images=[image], return_tensors="pt").to(
        "mps"
    )
    inputs["pixel_values"] = inputs["pixel_values"].to(torch.bfloat16)

    # Generate the captions
    generate_ids = llava_model.generate(
        **inputs,
        max_new_tokens=300,
        do_sample=True,
        suppress_tokens=None,
        use_cache=True,
        temperature=0.6,
        top_k=None,
        top_p=0.9,
    )[0]

    # Trim off the prompt
    generate_ids = generate_ids[inputs["input_ids"].shape[1] :]

    # Decode the caption
    caption = processor.tokenizer.decode(
        generate_ids, skip_special_tokens=True, clean_up_tokenization_spaces=False
    )
    caption = caption.strip()
    return caption


def generate_caption(image):
    # Build the conversation
    convo = [
        {
            "role": "system",
            "content": "You are a helpful image captioner.",
        },
        {
            "role": "user",
            "content": "Write a short descriptive caption for this image in a formal tone.",
        },
    ]

    return chat(convo, image)


def generate_tags(image):

    # Build the conversation
    convo = [
        {
            "role": "system",
            "content": "You are a helpful image tagger.",
        },
        {
            "role": "user",
            "content": "Write a short list of Booru tags for this image. Include whether the image is sfw, suggestive, or nsfw.",
        },
    ]

    return chat(convo, image)


if __name__ == "__main__":
    for image_path in sys.argv[1:]:
        with Image.open(image_path) as image:
            print(generate_caption(image))
            print(generate_tags(image))
