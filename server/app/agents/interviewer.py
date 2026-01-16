"""Interviewer agent for gathering learner context."""

import uuid

from pydantic import BaseModel, Field

from app.agents.base import BaseAgent
from app.agents.prompts import INTERVIEWER_SYSTEM_PROMPT
from app.agents.state import ExampleOption, InterviewQuestion


class InterviewQuestionsResponse(BaseModel):
    """Response schema for interview questions generation."""

    questions: list[dict] = Field(description="List of interview questions")


class InterviewerAgent(BaseAgent):
    """Agent that generates clarifying questions for the learner."""

    name = "interviewer"

    def get_system_prompt(self) -> str:
        return INTERVIEWER_SYSTEM_PROMPT

    async def generate_questions(
        self,
        topic: str,
        raw_input: str,
        title: str,
        max_questions: int = 5,
    ) -> list[InterviewQuestion]:
        """Generate clarifying questions based on the learning topic."""
        prompt = f"""Generate {max_questions} clarifying questions for a learner who wants to study:

Topic/Title: {title}

Their initial learning plan:
{raw_input}

For each question, provide:
- A clear question
- Brief purpose explaining why we're asking
- 2-3 example answers as options (with labels A, B, C)
- Whether freeform answers are allowed (usually true)

Output JSON:
{{
  "questions": [
    {{
      "question": "What is your current experience level with [topic]?",
      "purpose": "To calibrate the starting point of your roadmap",
      "example_options": [
        {{"label": "A", "text": "Complete beginner - never worked with it"}},
        {{"label": "B", "text": "Some exposure - done a few tutorials"}},
        {{"label": "C", "text": "Intermediate - built small projects"}}
      ],
      "allows_freeform": true
    }}
  ]
}}"""

        response = await self.generate_structured(
            prompt=prompt,
            response_model=InterviewQuestionsResponse,
        )

        questions = []
        for q in response.questions[:max_questions]:
            questions.append(
                InterviewQuestion(
                    id=f"q_{uuid.uuid4().hex[:8]}",
                    question=q.get("question", ""),
                    purpose=q.get("purpose", ""),
                    example_options=[
                        ExampleOption(label=opt.get("label", ""), text=opt.get("text", ""))
                        for opt in q.get("example_options", [])
                    ],
                    allows_freeform=q.get("allows_freeform", True),
                )
            )

        return questions
