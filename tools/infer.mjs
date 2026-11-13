import fs from "node:fs";
import { createRequire } from "node:module";
import { pathToFileURL } from "node:url";
import { performance } from "node:perf_hooks";

const [modelPath, promptPath, responsePath] = process.argv.slice(2);
const config = JSON.parse(fs.readFileSync(new URL("../model.json", import.meta.url)));
const npmRoot = process.env.TCC_NODE_ROOT;
const api = npmRoot
  ? await import(pathToFileURL(createRequire(npmRoot + "/package.json").resolve("node-llama-cpp")))
  : await import("node-llama-cpp");
const t = performance.now();
const llama = await api.getLlama({gpu: false, logLevel: "error", build: "never", skipDownload: true});
try {
  const model = await llama.loadModel({modelPath});
  const ctx = await model.createContext({contextSize: config.context, threads: config.threads});
  const session = new api.LlamaChatSession({
    contextSequence: ctx.getSequence(),
    systemPrompt: "Write small deterministic RSpec unit tests from the given specification. Return Ruby only."
  });
  const loadSeconds = (performance.now() - t)/1000;
  const start = performance.now();
  const input = fs.readFileSync(promptPath, "utf8");
  const reply = await session.promptWithMeta(input, {
    temperature: config.temperature, seed: config.seed, maxTokens: config.max_output_tokens
  });
  fs.writeFileSync(responsePath, reply.responseText);
  process.stdout.write(JSON.stringify({
    load_seconds: loadSeconds, inference_seconds: (performance.now()-start)/1000,
    stop_reason: reply.stopReason
  })+"\n");
} finally {
  await llama.dispose();
}
