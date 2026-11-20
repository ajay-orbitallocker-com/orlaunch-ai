GENERATION_MODEL = "gpt-5.4-mini"
GENERATION_TOP_K = 5

# Template selection: the AI reads the idea and picks the template labels.
TEMPLATE_SELECTION_MODEL = GENERATION_MODEL
TEMPLATE_SELECTION_MAX_ATTEMPTS = 2   # first try plus one retry

# Outline planning: the AI plans assessments, extra sections, order and headings.
OUTLINE_MODEL = GENERATION_MODEL
OUTLINE_MAX_ATTEMPTS = 2              # first try plus one retry