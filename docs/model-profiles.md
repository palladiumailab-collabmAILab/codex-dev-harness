# Model profiles

モデル固有指示は共通 `AGENTS.md` に混在させません。

- GPT-6 Astra -> `profiles/astra/AGENTS.md`
- GPT-5.6 Sol / Luna -> `profiles/sol-luna/AGENTS.md`

rootは不変条件とroutingだけを持ち、対応profileを1つだけ読みます。skill/baselineも発火条件に一致したものだけを読みます。

Sol/Lunaでは worker 利用そのものを目的にせず、handoff・再読込を含む総context/往復が減る場合だけ Luna へ委譲します。Astraでは必要なguidanceの遅延読込と、大きなtool observationの重複投入回避を優先します。

一次資料:
- OpenAI Developers, “Rethinking skills and prompts for GPT-6 Astra”
  https://developers.openai.com/blog/rethinking-skills-and-prompts-for-gpt-6-astra
