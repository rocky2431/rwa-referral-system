/// <reference types="vite/client" />

interface ImportMetaEnv {
  readonly VITE_API_BASE_URL: string
  readonly VITE_CONTRACT_ADDRESS: string
  readonly VITE_BSC_NETWORK: string
  readonly VITE_BSC_TESTNET_RPC: string
  readonly VITE_BSC_MAINNET_RPC: string
  readonly VITE_APP_NAME: string
  readonly VITE_APP_URL: string
}

interface ImportMeta {
  readonly env: ImportMetaEnv
}
