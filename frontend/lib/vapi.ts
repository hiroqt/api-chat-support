import Vapi from "@vapi-ai/web";

let vapiInstance: Vapi | null = null;
let currentKey: string | null = null;

export const getVapiClient = (): Vapi => {
  if (typeof window === "undefined") {
    throw new Error("Vapi web client cannot be initialized on the server.");
  }

  const publicKey = process.env.NEXT_PUBLIC_VAPI_PUBLIC_KEY;

  if (!publicKey) {
    throw new Error("NEXT_PUBLIC_VAPI_PUBLIC_KEY is not defined in environment variables.");
  }

  // If key changed or instance not created yet, re-instantiate
  if (!vapiInstance || currentKey !== publicKey) {
    currentKey = publicKey;
    vapiInstance = new Vapi(publicKey);
  }

  return vapiInstance;
};
