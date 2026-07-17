from typing import Annotated

from pydantic import BaseModel, Field, StringConstraints

ResumeContent = Annotated[
    str,
    StringConstraints(strip_whitespace=True, min_length=1, max_length=100_000),
]


class ResumeAnalysisRequest(BaseModel):
    resume_text: ResumeContent = Field(description="The candidate's resume text")
    job_description: ResumeContent = Field(description="The target job description")


class ResumeAnalysisResponse(BaseModel):
    score: int = Field(ge=0, le=100, description="Overall resume-to-job match score")
    matching_skills: list[str] = Field(
        default_factory=list,
        description="Skills supported by the resume and required by the job",
    )
    missing_skills: list[str] = Field(
        default_factory=list,
        description="Important job requirements not evidenced by the resume",
    )
    resume_advices: list[str] = Field(
        default_factory=list,
        description="Specific and actionable resume improvements",
    )
    interview_questions: list[str] = Field(
        default_factory=list,
        description="Likely interview questions based on the job and identified gaps",
    )
