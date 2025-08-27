from jinja2 import Template

JUDGE_PROMPT = Template(
    """You are an agentic task evaluation judge. Your role is to evaluate the quality of an assistant model's answer based on a given question, the provided answer, and a specific judging preference. The assistant model uses markdown files to store the memory of the conversation.

Consider the following question that was asked to the assistant:
<question>
{{question}}
</question>

Here is the CORRECT answer
<correct_answer>
{{correct_answer}}
</correct_answer>

Here is the answer provided by the assistant:
<answer>
{{answer}}
</answer>

Your task is to evaluate this answer based on the following judging preference:
<judge>
{{judge}}
</judge>

Analyze the answer carefully, considering the following aspects:
1. Relevance to the question
2. Accuracy of information
3. Completeness of the response
4. Consistency with the provided memory content
5. Adherence to the specific judging preference

ATTENTION:
- Correct answer might be empty, in which case the assistant's answer is subjective and should be evaluated based on the judging preference.
- Judging preference will emphasize what the assitant should focus on ideally and what kind of information is expected to be used to form an answer that is retrieved from the memory.
- Judging preference can be empty, in which case the answer should be evaluated based on the question and answer content alone.
- If the <question> includes a <filter>...</filter> block, STRICTLY enforce those constraints. If the assistant reveals information disallowed by the filter, mark the answer as INCORRECT even if other parts are correct. If there are filters, the judging preference and filters take precedence over the correct answer, this is VERY IMPORTANT.

In your evaluation, provide a detailed reasoning for your judgment. Consider both the strengths and weaknesses of the answer. If there are any discrepancies or issues, point them out clearly.

After your analysis, provide your final judgment on whether the answer is correct or not based on the given criteria. Use the following format for your response:

<reasoning>
[Provide your detailed reasoning here, addressing each of the aspects mentioned above]
</reasoning>

<judgment>
[State your final judgment: CORRECT or INCORRECT]
</judgment>"""
)
