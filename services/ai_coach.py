import os

from services.rag import InterviewKnowledgeBase


TRACKS = [
    {"id": "software-engineering", "title": "Software engineering", "category": "Tech", "icon": "</>", "description": "Algorithms, system design, and practical coding judgement.", "color": "azure"},
    {"id": "data-analytics", "title": "Data & analytics", "category": "Tech", "icon": "◫", "description": "SQL, insight storytelling, and business analysis.", "color": "violet"},
    {"id": "product-management", "title": "Product management", "category": "Tech", "icon": "◇", "description": "Strategy, prioritisation, and product sense.", "color": "orange"},
    {"id": "consulting", "title": "Consulting", "category": "Non-tech", "icon": "↗", "description": "Case structure, communication, and commercial thinking.", "color": "green"},
    {"id": "sales", "title": "Sales & business development", "category": "Non-tech", "icon": "◎", "description": "Discovery, objections, and customer value.", "color": "pink"},
    {"id": "hr", "title": "People & HR", "category": "Non-tech", "icon": "♧", "description": "Behavioural questions and people-first judgement.", "color": "blue"},
]

QUESTIONS = {
    "software-engineering": "You are designing a URL shortener for a rapidly growing product. How would you structure it for reliability and scale?",
    "data-analytics": "A dashboard shows weekly conversions falling by 12%. Talk me through how you would investigate the change.",
    "product-management": "A key feature has high sign-ups but low week-two retention. What would you do first, and why?",
    "consulting": "A regional coffee chain has seen profits decline for three quarters. How would you structure your initial analysis?",
    "sales": "A prospect says their current provider is good enough and they have no budget. How would you move the conversation forward?",
    "hr": "Tell me about a time you had to handle disagreement between two team members. What was your approach?",
}


class InterviewCoach:
    def __init__(self):
        self.endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")
        self.api_key = os.getenv("AZURE_OPENAI_API_KEY")
        self.deployment = os.getenv("AZURE_OPENAI_DEPLOYMENT")
        self.knowledge = InterviewKnowledgeBase()

    @property
    def uses_foundry_endpoint(self):
        """True for any Microsoft Foundry / Azure AI Foundry endpoint.

        Foundry endpoints may contain:
          - .services.ai.azure.com  (classic AI Services projects)
          - /openai/v1              (newer Foundry project endpoints)
          - /v1                     (generic v1-style paths)
        The key symptom: they require the plain OpenAI client (no api-version param).
        """
        if not self.endpoint:
            return False
        ep = self.endpoint.rstrip("/")
        return (
            ".services.ai.azure.com" in ep
            or ep.endswith("/v1")
            or "/openai/v1" in ep
        )

    def interview_tracks(self):
        return TRACKS

    def get_track(self, track_id):
        return next((track for track in TRACKS if track["id"] == track_id), None)

    def opening_question(self, track):
        return QUESTIONS[track["id"]]

    def _completion(self, messages):
        if not (self.endpoint and self.deployment):
            return None
        try:
            if self.uses_foundry_endpoint:
                from openai import OpenAI

                # Ensure base_url ends at the /v1 root (no trailing slash, no /chat/completions)
                base_url = self.endpoint.rstrip("/")
                # Remove any extra path segments beyond /v1
                for suffix in ("/responses", "/chat/completions", "/completions"):
                    if base_url.endswith(suffix):
                        base_url = base_url[: -len(suffix)]

                if self.api_key:
                    client = OpenAI(base_url=base_url, api_key=self.api_key)
                else:
                    # Fall back to Azure CLI / managed identity
                    from azure.identity import DefaultAzureCredential, get_bearer_token_provider
                    token_provider = get_bearer_token_provider(
                        DefaultAzureCredential(), "https://ai.azure.com/.default"
                    )
                    client = OpenAI(base_url=base_url, api_key=token_provider())

                # Foundry /v1 endpoints use the standard chat completions API —
                # NOT the Responses API, and NOT AzureOpenAI (which adds api-version).
                response = client.chat.completions.create(
                    model=self.deployment,
                    messages=messages,
                    temperature=0.65,
                    max_tokens=500,
                )
                return response.choices[0].message.content

            if not self.api_key:
                return None
            from openai import AzureOpenAI
            client = AzureOpenAI(
                api_key=self.api_key,
                api_version=os.getenv("AZURE_OPENAI_API_VERSION", "2024-10-21"),
                azure_endpoint=self.endpoint,
            )
            response = client.chat.completions.create(
                model=self.deployment, messages=messages, temperature=0.65, max_tokens=500
            )
            return response.choices[0].message.content
        except Exception as e:
            print(f"[ai_coach] completion failed: {e}")
            return None

    def evaluate_answer(self, track, answer, history):
        references = self.knowledge.retrieve(f"{track['title']} interview coaching {answer}")
        grounding = "\n\nGrounding notes from the PrepMate knowledge base:\n" + "\n".join(references) if references else ""
        prompt = [
            {"role": "system", "content": f"You are PrepMate, an encouraging but exacting AI coaching agent for {track['title']}. Give concise feedback: what worked, one improvement, then ask one follow-up interview question. Do not pretend the candidate said facts they did not say.{grounding}"},
            {"role": "user", "content": f"Interview question: {self.opening_question(track)}\nCandidate answer: {answer}"},
        ]
        response = self._completion(prompt)
        if response:
            return response
        strengths = "You gave a clear starting point" if len(answer.split()) > 25 else "You got to the point quickly"
        return f"{strengths}. To make this stronger, use a simple structure: situation, decision, evidence, and outcome. Add one specific example or measurable result.\n\nFollow-up: What trade-off would you make if time and resources were limited?"

    def answer_question(self, prompt, history):
        references = self.knowledge.retrieve(prompt)
        grounding = "\n\nUse these retrieved PrepMate references when relevant:\n" + "\n".join(references) if references else ""
        messages = [{"role": "system", "content": f"You are PrepMate, an AI interview coaching agent. Give practical, accurate preparation advice for both tech and non-tech roles. Be warm, concise, and use examples when helpful.{grounding}"}]
        for item in history[-8:]:
            messages.append({"role": "assistant" if item["role"] == "coach" else "user", "content": item["content"]})
        messages.append({"role": "user", "content": prompt})
        response = self._completion(messages)
        if response:
            return response
        return "A solid way to approach that is to make your answer specific and evidence-led. Start with the context, explain the action you personally took, and close with the result. For an interview answer, prepare one concise example you can adapt, then practise saying it aloud in under two minutes."
