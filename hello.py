def classify(name):
    n = str(name).lower()
    if "copil" in n or "копилот" in n: return "Self/copilot"
    if "self" in n or "селф" in n: return "Self"
    if "vox" in n or "вокс" in n: return "Vox"
    if "нац." in n or "нац " in n: return "Vox/нац.при"
    return "Hybrid"

# Давай проверим сразу несколько имен
examples = ["ООО Копилот", "Self-service", "нац проект", "Просто компания"]

for item in examples:
    print(f"{item} -> {classify(item)}")