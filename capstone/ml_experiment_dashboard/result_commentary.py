from langchain_google_genai import ChatGoogleGenerativeAI
from django.conf import settings


def _extract_text(content):
    """LangChain chat models return `.content` as either a plain string or a
    list of content blocks (e.g. Gemini 3.x includes a 'text' block alongside
    an opaque thought-signature block). Normalize to plain text either way."""
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        return "".join(
            block.get("text", "")
            for block in content
            if isinstance(block, dict) and block.get("type") == "text"
        )
    return str(content)

def generate_result_commentary(result_data):
    # Extract relevant information from the result_data dictionary
    model_name = result_data.get("model", "Unknown Model")
    target_column = result_data.get("target_column", "Unknown Target")
    feature_columns = result_data.get("feature_columns", [])
    metric_name = result_data.get("metric_name", "Unknown Metric")
    metric_value = result_data.get("metric_value", "Unknown Value")

    prompt = (
        "You are summarizing the results of a machine learning experiment. Do not "
        "make up information.\n\n"
        f"Model: {model_name}\n"
        f"Target column (what it predicts): {target_column}\n"
        f"Feature columns used: {', '.join(feature_columns)}\n"
        f"Metric: {metric_name} = {metric_value}\n\n"
        "Write a short summary (3-5 sentences) covering:\n " \
        "1. What the model is and what it was trained to do.\n" \
        "2. How well the model performed based on the metric provided.\n" \
        "3. Any potential next steps or considerations for improving the model's performance."
    )

    model = ChatGoogleGenerativeAI(
        model="gemini-3.6-flash",
        google_api_key=settings.GOOGLE_API_KEY,
    )
    response = model.invoke(prompt)
    return _extract_text(response.content)