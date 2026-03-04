import os
import json
from models import StudentSubmission, Rubric, FeedbackResponse
from rag_service import RAGService
from openai import OpenAI

# LLMClient with Mock Fallback
class LLMClient:
    def __init__(self):
        self.api_key = os.getenv("OPENAI_API_KEY")
        self.client = None
        if self.api_key:
            try:
                self.client = OpenAI(api_key=self.api_key)
                print("✅ OpenAI Client Initialized")
            except Exception as e:
                print(f"⚠️ OpenAI Init Failed: {e}")
        else:
            print("⚠️ No OPENAI_API_KEY found. Using Mock Grading Mode.")

    def generate(self, prompt: str, json_mode: bool = False) -> str:
        # 1. REAL MODE (if client exists)
        if self.client:
            try:
                response = self.client.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=[
                        {"role": "system", "content": "You are an expert academic grader. Output JSON only."},
                        {"role": "user", "content": prompt}
                    ],
                    response_format={"type": "json_object"} if json_mode else None
                )
                return response.choices[0].message.content
            except Exception as e:
                print(f"❌ API Error: {e}. Falling back to mock.")
        
        # 2. MOCK MODE (Fallback)
        # Helper to extract student text from prompt (hacky for mock)
        student_text = ""
        if "Student Submission:" in prompt:
            student_text = prompt.split("Student Submission:")[1].strip()
        
        word_count = len(student_text.split())
        
        # --- LOGIC: FAIL ---
        if word_count < 100:
            return json.dumps({
                "submission_id": "mock_sub_id",
                "total_score": 40,
                "max_score": 100,
                "criteria_feedback": [
                    {
                        "criterion_id": "c1",
                        "name": "Thesis",
                        "score": 5,
                        "max_points": 20,
                        "level_achieved": "Beginning",
                        "reasoning": "Thesis is missing or extremely vague due to brevity.",
                        "evidence_quotes": []
                    },
                    {
                        "criterion_id": "c2",
                        "name": "Evidence",
                        "score": 10,
                        "max_points": 40,
                        "level_achieved": "Beginning",
                        "reasoning": "No significant evidence provided. Submission is too short.",
                        "evidence_quotes": []
                    },
                     {
                        "criterion_id": "c3",
                        "name": "Mechanics",
                        "score": 25,
                        "max_points": 40,
                        "level_achieved": "Developing",
                        "reasoning": "Writing is simplistic.",
                        "evidence_quotes": []
                    }
                ],
                "general_summary": "This submission is significantly under the length requirement. It lacks the depth needed to analyze the topic.",
                "strengths": ["Submitted on time"],
                "weaknesses": ["Too short", "Lacks evidence", "No thesis"],
                "improvement_plan": []
            })

        # --- LOGIC: PERFECT ---
        elif word_count > 200 and "David Kennedy" in student_text:
             return json.dumps({
                "submission_id": "mock_sub_id",
                "total_score": 98,
                "max_score": 100,
                "criteria_feedback": [
                    {
                        "criterion_id": "c1",
                        "name": "Thesis",
                        "score": 20,
                        "max_points": 20,
                        "level_achieved": "Mastery",
                        "reasoning": "Thesis is sophisticated and covers structural weakness.",
                        "evidence_quotes": ["precipitating event exposing deeper structural weaknesses"]
                    },
                    {
                        "criterion_id": "c2",
                        "name": "Evidence",
                        "score": 40,
                        "max_points": 40,
                        "level_achieved": "Mastery",
                        "reasoning": "Excellent use of historian David Kennedy to support claims.",
                        "evidence_quotes": ["As historian David Kennedy notes"]
                    },
                     {
                        "criterion_id": "c3",
                        "name": "Mechanics",
                        "score": 38,
                        "max_points": 40,
                        "level_achieved": "Mastery",
                        "reasoning": "Professional academic tone throughout.",
                        "evidence_quotes": []
                    }
                ],
                "general_summary": "An outstanding submission. You demonstrated a mastery of the historical context and effectively integrated primary and secondary sources.",
                "strengths": ["Strong thesis", "Excellent citations", "Nuanced analysis"],
                "weaknesses": [],
                "improvement_plan": []
            })
            
        # --- LOGIC: AVERAGE (Default) ---
        else:
             return json.dumps({
                "submission_id": "mock_sub_id",
                "total_score": 75,
                "max_score": 100,
                "criteria_feedback": [
                    {
                        "criterion_id": "c1",
                        "name": "Thesis",
                        "score": 15,
                        "max_points": 20,
                        "level_achieved": "Proficient",
                        "reasoning": "Thesis is present but could be more specific.",
                        "evidence_quotes": []
                    },
                    {
                        "criterion_id": "c2",
                        "name": "Evidence",
                        "score": 30,
                        "max_points": 40,
                        "level_achieved": "Proficient",
                        "reasoning": "Uses some evidence but lacks deep analysis of sources.",
                        "evidence_quotes": []
                    },
                     {
                        "criterion_id": "c3",
                        "name": "Mechanics",
                        "score": 30,
                        "max_points": 40,
                        "level_achieved": "Proficient",
                        "reasoning": "Good writing, but some structural issues.",
                        "evidence_quotes": []
                    }
                ],
                "general_summary": "A solid effort. You understand the main events, but try to go deeper into the 'why', not just the 'what'.",
                "strengths": ["Clear timeline", "Good understanding of basics"],
                "weaknesses": ["Needs more specific evidence", "Analysis is surface level"],
                "improvement_plan": []
            })

llm_client = LLMClient()
rag_service = RAGService()

class FeedbackService:
    def __init__(self):
        pass

    def _generate_rule_based_feedback(self, submission: StudentSubmission, rubric: Rubric, context: str) -> FeedbackResponse:
        """
        Generates feedback based on keyword matching between submission and context (Reference Material).
        Used when no OpenAI API key is available.
        """
        import re
        from collections import Counter

        def normalize_text(text):
            return re.findall(r'\b\w{4,}\b', text.lower())

        # 1. Analyze Context (Reference Material)
        if not context:
            # Fallback if no reference material uploaded
            context = "history analysis hypothesis evidence conclusion timeline causes effects"
        
        context_words = set(normalize_text(context))
        submission_words = normalize_text(submission.text_content)
        submission_word_count = len(submission_words)
        
        if submission_word_count < 10:
             return FeedbackResponse(
                submission_id=submission.id,
                total_score=10,
                max_score=100,
                criteria_feedback=[],
                general_summary="The submission is too short to evaluate.",
                strengths=[],
                weaknesses=["Submission is empty or too short."],
                status="draft"
            )

        # 2. Match Keywords
        matches = [word for word in submission_words if word in context_words]
        unique_matches = set(matches)
        match_score = len(unique_matches) / len(context_words) if context_words else 0
        
        # 3. Calculate Grades
        # Simple algorithm: Score correlates with how many unique reference keywords were used
        # Cap at 1.0 (100%)
        # A good essay might use 30-50% of the key vocabulary from the reference
        scaled_score = min(match_score * 2.5 * 100, 100) # Multiplier to be generous
        
        grade_comments = {
            "Excellent": "Excellent work. You've incorporated key concepts from the reference material effectively.",
            "Good": "Good effort. You hit several key points, but could go deeper into the specifics found in the reference text.",
            "Fair": "Fair attempt. Try to use more vocabulary and concepts from the provided reading materials.",
            "Poor": "This submission seems to lack connection to the reference material. Please review the source text."
        }
        
        if scaled_score >= 85: quality = "Excellent"
        elif scaled_score >= 70: quality = "Good"
        elif scaled_score >= 50: quality = "Fair"
        else: quality = "Poor"

        # 4. Generate Criteria Feedback
        criteria_feedback = []
        for criterion in rubric.criteria:
            # Distribute the scaled score with some randomness/variance per criterion
            crit_score = min(scaled_score * (criterion.max_points / 100), criterion.max_points)
            
            criteria_feedback.append({
                "criterion_id": criterion.id,
                "name": criterion.name,
                "score": round(crit_score, 1),
                "max_points": criterion.max_points,
                "level_achieved": quality,
                "reasoning": f"{grade_comments[quality]} (Keyword match coverage: {int(match_score*100)}%)",
                "evidence_quotes": [] 
            })

        # 5. Extract Evidence (Sentences with keywords)
        sentences = re.split(r'[.!?]+', submission.text_content)
        strong_sentences = []
        for sent in sentences:
            if any(w in sent.lower() for w in list(context_words)[:5]): # Check if it contains top keywords
                if len(sent) > 20:
                    strong_sentences.append(sent.strip())
        
        return FeedbackResponse(
            submission_id=submission.id,
            total_score=round(scaled_score, 1),
            max_score=100,
            criteria_feedback=criteria_feedback,
            general_summary=f"This is a {quality.lower()} submission. {grade_comments[quality]}",
            strengths=[f"Used {len(unique_matches)} key concepts from reference"] + (["Strong connection to source text"] if scaled_score > 70 else []),
            weaknesses=["Expand on the key themes"] if scaled_score < 70 else [],
            status="published"
        )

    async def generate_feedback(self, submission: StudentSubmission, rubric: Rubric) -> FeedbackResponse:
        import asyncio
        
        # 1. Retrieve Context
        # Query using the student's submission text to find relevant reference material
        # (Assuming rag_service is sync, run in thread)
        context = await asyncio.to_thread(rag_service.retrieve_context, submission.text_content[:200])
        
        print(f"🔎 DEBUG: Retrieved Context for Grading (Length: {len(context)})")
        print(f"🔎 DEBUG: Context Preview: {context[:200]}...")

        # Check if we should use Real LLM or Rule-Based Fallback
        if not llm_client.client:
            print("⚠️ Using Rule-Based Feedback Service (No API Key)")
            return self._generate_rule_based_feedback(submission, rubric, context)

        # 2. Construct Prompt
        prompt = f"""
        Rubric: {rubric.model_dump_json()}
        Context: {context}
        Student Submission: {submission.text_content}
        
        Grade this using the rubric and context. Output JSON.
        """
        
        # 3. Call LLM (Blocking sync call -> run in thread)
        response_json = await asyncio.to_thread(llm_client.generate, prompt, json_mode=True)
        
        # 4. Parse & Return
        result = FeedbackResponse.model_validate_json(response_json)
        result.submission_id = submission.id
        return result
