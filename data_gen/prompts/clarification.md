You are creating training data for an LLM agent with a self-managed, Obsidian-like memory system. Given the user's memory below, synthesize ONE realistic user question and the ideal assistant reply for the specified clarification scenario. Do not invent fixed content in the reply; the reply should ask for missing specifics or resolve contradictions without hallucinating facts.

Memory (partial):
{memory}

Requirements by scenario:
- non_existing_entity: The question should reference an entity that is NOT present in memory. The reply should state the entity isn't found in memory and ask the user to confirm or provide details.
- non_existing_attribute: The question should ask for an attribute that is NOT present for an EXISTING entity in memory. The reply should note the attribute is missing and ask a pointed follow-up (e.g., which value).
- contradiction: The question should contain a detail that contradicts memory. The reply should point out the specific mismatch and ask the user which version is correct.

Output constraints:
- Keep question and answer concise and natural (1-2 sentences each).
- Do not mention having tool access or external systems; focus on clarifying the information.
- The answer must not include code fences or special tags.

Now generate ONE sample for scenario='{scenario}'. Return strictly as JSON matching this schema:
{ 'question': str, 'answer': str, 'rationale': str? }
