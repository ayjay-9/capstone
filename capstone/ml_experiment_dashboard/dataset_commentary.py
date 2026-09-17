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


def generate_dataset_commentary(df):
    columns = df.columns.tolist()
    row_count = len(df)
    numeric_columns = df.select_dtypes(include="number").columns.tolist()
    categorical_columns = [column for column in columns if column not in numeric_columns]

    missing_counts = df.isnull().sum()
    missing_summary = {
        column: int(count) for column, count in missing_counts.items() if count > 0
    }
    duplicate_count = int(df.duplicated().sum())

    numeric_stats = {
        column: {
            "min": float(df[column].min()),
            "max": float(df[column].max()),
            "mean": round(float(df[column].mean()), 2),
        }
        for column in numeric_columns
    }

    prompt = (
        "You are summarizing a dataset a user just uploaded to an ML experiment "
        "dashboard. Use only the facts below - do not guess at or invent values "
        "you were not given.\n\n"
        f"Row count: {row_count}\n"
        f"Numeric columns: {numeric_columns}\n"
        f"Categorical columns: {categorical_columns}\n"
        f"Numeric column stats (min/max/mean): {numeric_stats}\n"
        f"Missing values per column (only columns with missing values are listed): {missing_summary}\n"
        f"Duplicate rows: {duplicate_count}\n\n"
        "Write a short summary (4-6 sentences) covering:\n"
        "1. What this dataset appears to represent.\n"
        "2. Which column looks like the most natural prediction target for a "
        "machine learning model, and which columns could be used to predict it.\n"
        "3. Any data quality issues visible in the facts above (missing values, "
        "duplicate rows) - if there are none, say so plainly rather than inventing any."
    )

    model = ChatGoogleGenerativeAI(
        model="gemini-3.6-flash",
        google_api_key=settings.GOOGLE_API_KEY,
    )
    response = model.invoke(prompt)
    return _extract_text(response.content)
