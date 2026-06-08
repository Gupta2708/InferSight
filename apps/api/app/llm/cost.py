PRICING = {
    ("mock", "mock-fast"): (0.0, 0.0),
    ("mock", "mock-slow"): (0.0, 0.0),
    ("openai", "gpt-4.1-mini"): (0.0004, 0.0016),
    ("openai", "gpt-4o-mini"): (0.00015, 0.0006),
    ("gemini", "gemini-flash"): (0.000075, 0.0003),
    ("gemini", "gemini-1.5-flash"): (0.000075, 0.0003),
    ("gemini", "gemini-2.0-flash"): (0.0001, 0.0004),
}


def estimate_cost(provider: str, model: str, input_tokens: int, output_tokens: int) -> tuple[float, float, float]:
    input_rate, output_rate = PRICING.get((provider, model), (0.0, 0.0))
    input_cost = (input_tokens / 1000) * input_rate
    output_cost = (output_tokens / 1000) * output_rate
    return round(input_cost, 8), round(output_cost, 8), round(input_cost + output_cost, 8)
