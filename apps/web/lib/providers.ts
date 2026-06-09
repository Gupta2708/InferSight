import type { ProviderModel } from "./types";

export function getModelsForProvider(models: ProviderModel[], provider: string) {
  return models.filter((m) => m.provider === provider && m.enabled);
}

export function getDefaultModelForProvider(models: ProviderModel[], provider: string) {
  const list = getModelsForProvider(models, provider);
  return list.length ? list[0].model : "";
}

export function isValidProviderModel(models: ProviderModel[], provider: string, model: string) {
  return getModelsForProvider(models, provider).some((m) => m.model === model);
}
