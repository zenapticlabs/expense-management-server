from pathlib import Path
import re
from typing import List
import fitz
from langchain_openai import ChatOpenAI
from langchain.chains import LLMChain
from langchain.prompts import ChatPromptTemplate
from common.models import Airline, CarType, MealCategory, RelationshipToPAI, City, HotelDailyBaseRate, MileageRate, ExchangeRate, RentalAgency
import json
import base64


vision_llm = ChatOpenAI(model="gpt-4o", temperature=0)

def match_or_none(model, field_value, field_name="name"):
    """Utility to match extracted value against a model field, return None if no match."""
    if not field_value:
        return None
    try:
        # Use case-insensitive match to improve accuracy
        return model.objects.filter(**{f"{field_name}__iexact": field_value.strip()}).first()
    except Exception:
        return None
    
def encode_image_to_base64(image_path: str) -> str:
    """Encode an image to base64 format with data URI prefix."""
    ext = Path(image_path).suffix.lower().replace('.', '')
    mime_type = f"image/{'jpeg' if ext in ['jpg', 'jpeg'] else ext}"
    with open(image_path, "rb") as f:
        base64_str = base64.b64encode(f.read()).decode("utf-8")
    return base64_str, mime_type


def encode_image_bytes_to_base64(png_bytes: bytes) -> str:
    """Encode PNG bytes to base64 string with data URI."""
    return base64.b64encode(png_bytes).decode("utf-8")


def create_ocr_prompt(base64_image: str, mime_type: str):
    """Generate a ChatPromptTemplate with embedded base64 image."""
    return ChatPromptTemplate.from_messages([
        ("system", """
            You are an intelligent OCR and data extraction assistant.
            Follow Exact Intructions, Be Strict
            Look at the provided receipt image and return a structured JSON with these fields:
            - merchant
            - expense_date
            - expense_type
            - receipt_amount
            - receipt_currency (only: USD, CAD, JPY)
            - justifications
            - note
            - origin_destination
            - employee_names
            - company_customer_name_title
            - business_topic
            - total_attendees
            - name_of_establishment
            - hotel_name
            - carrier
            - distance
            - airline
            - city
            - car_type
            - hotel_daily_base_rate
            - meal_category
            - mileage_rate
            - relationship_to_pai
            - rental_agency (set to 'Other' if unrecognized)
            - attendee1 to attendee10
            - payment_method (Cash or Credit Card only)
            - exchange_rate

            Ignore blurry or irrelevant text. Be accurate and concise.
            Return a clean JSON object.
        """),
        {
            "role": "user",
            "content": [
                {
                    "type": "image_url",
                    "image_url": {
                        "url": f"data:{mime_type};base64,{base64_image}"
                    }
                }
            ]
        }
    ])



def clean_and_parse_json(raw_output: str) -> dict:
    try:
        # Remove markdown code block if present
        cleaned = re.sub(r"^```(?:json)?\s*|\s*```$", "", raw_output.strip(), flags=re.MULTILINE)
        return json.loads(cleaned)
    except json.JSONDecodeError as e:
        print("Failed to parse JSON:", e)
        print("Raw model output:\n", raw_output)
        return {"error": "Failed to parse structured info as JSON."}
    


def pdf_to_png_bytes(pdf_bytes: bytes, zoom: float = 2.0) -> List[bytes]:
    """Convert PDF bytes to list of PNG bytes (1 per page)."""
    png_bytes_list = []
    with fitz.open(stream=pdf_bytes, filetype="pdf") as pdf:
        for page_number in range(len(pdf)):
            page = pdf.load_page(page_number)
            mat = fitz.Matrix(zoom, zoom)
            pix = page.get_pixmap(matrix=mat)
            png_bytes = pix.tobytes("png")
            png_bytes_list.append(png_bytes)
    return png_bytes_list


def process_pdf_bytes(pdf_bytes: bytes) -> dict:
    """Main OCR processing from PDF bytes."""
    png_pages = pdf_to_png_bytes(pdf_bytes)
    if not png_pages:
        return {"error": "PDF contains no pages or failed to render."}

    # Use first page only (you can iterate over multiple pages if needed)
    base64_image = encode_image_bytes_to_base64(png_pages[0])
    prompt = create_ocr_prompt(base64_image)

    chain = LLMChain(llm=vision_llm, prompt=prompt)

    try:
        structured_info_raw = chain.run({})
        extracted_info = clean_and_parse_json(structured_info_raw)
        return {"extracted_info": extracted_info}
    except Exception as e:
        return {"error": f"LLM processing failed: {e}"}
    

def process_receipt(file_path: str) -> dict:
    """Process a receipt (PDF or image) and return structured structured data."""
    suffix = Path(file_path).suffix.lower()
    
    try:
        if suffix == ".pdf":
            # Convert PDF to PNG bytes
            with open(file_path, "rb") as f:
                pdf_bytes = f.read()
            png_pages = pdf_to_png_bytes(pdf_bytes)
            if not png_pages:
                return {"error": "PDF contains no pages or failed to render."}
            base64_image = encode_image_bytes_to_base64(png_pages[0])
            mime_type = "image/png"
        else:
            # Handle image normally
            base64_image, mime_type = encode_image_to_base64(file_path)

        # Create and run LLM chain
        prompt = create_ocr_prompt(base64_image, mime_type)
        chain = LLMChain(llm=vision_llm, prompt=prompt)
        structured_info_raw = chain.run({})
        extracted_info = clean_and_parse_json(structured_info_raw)

    except Exception as e:
        return {"error": f"Failed to process file: {e}"}

    # Match related models
    rental_agency = match_or_none(RentalAgency, extracted_info.get("rental_agency"))
    rental_agency = rental_agency if rental_agency else "Other"

    matched_info = {
        **extracted_info,
        "airline": match_or_none(Airline, extracted_info.get("airline")),
        "car_type": match_or_none(CarType, extracted_info.get("car_type")),
        "meal_category": match_or_none(MealCategory, extracted_info.get("meal_category")),
        "relationship_to_pai": match_or_none(RelationshipToPAI, extracted_info.get("relationship_to_pai")),
        "city": match_or_none(City, extracted_info.get("city")),
        "hotel_daily_base_rate": match_or_none(HotelDailyBaseRate, extracted_info.get("hotel_daily_base_rate")),
        "mileage_rate": match_or_none(MileageRate, extracted_info.get("mileage_rate")),
        "exchange_rate": match_or_none(ExchangeRate, extracted_info.get("exchange_rate")),
        "rental_agency": rental_agency,
    }

    return {
        "extracted_info": matched_info
    }
