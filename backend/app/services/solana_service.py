import asyncio
import base64
import logging
import os
from threading import Lock
from uuid import UUID

from solana.rpc.async_api import AsyncClient
from solders.instruction import AccountMeta, Instruction
from solders.keypair import Keypair
from solders.message import Message
from solders.pubkey import Pubkey
from solders.transaction import Transaction

logger = logging.getLogger(__name__)

MEMO_PROGRAM_ID = Pubkey.from_string("MemoSq4gqABAXKb96qnH8TysNcWxMyWCqXgDLGmfcHr")
DEFAULT_RPC_URL = "https://api.devnet.solana.com"
EXPLORER_URL_TEMPLATE = "https://explorer.solana.com/tx/{signature}?cluster=devnet"


class SolanaService:
    def __init__(self) -> None:
        self.rpc_url = os.getenv("SOLANA_RPC_URL", DEFAULT_RPC_URL)
        secret_b64 = os.getenv("SOLANA_WALLET_SECRET_B64")
        self.enabled = bool(secret_b64)
        self.keypair: Keypair | None = None
        self._cache: dict[UUID, str] = {}
        self._lock = Lock()
        if self.enabled:
            try:
                self.keypair = Keypair.from_bytes(base64.b64decode(secret_b64))
            except Exception as exc:  # noqa: BLE001 - defensive: malformed key shouldn't crash startup
                logger.warning("Invalid SOLANA_WALLET_SECRET_B64: %s", exc)
                self.enabled = False

    def record_completion(self, simulation_id: UUID, outcome: str, overall_score: int) -> str | None:
        if not self.enabled or self.keypair is None:
            return None

        with self._lock:
            cached = self._cache.get(simulation_id)
        if cached is not None:
            return cached

        memo_text = f"Hurricane Week | sim={simulation_id} | outcome={outcome} | score={overall_score}/100"

        try:
            explorer_url = asyncio.run(self._send_memo(memo_text))
        except Exception as exc:  # noqa: BLE001 - external RPC, never let this break the report
            logger.warning("Solana memo transaction failed: %s", exc)
            return None

        if explorer_url:
            with self._lock:
                self._cache[simulation_id] = explorer_url
        return explorer_url

    async def _send_memo(self, memo_text: str) -> str | None:
        client = AsyncClient(self.rpc_url)
        try:
            instruction = Instruction(
                program_id=MEMO_PROGRAM_ID,
                accounts=[AccountMeta(pubkey=self.keypair.pubkey(), is_signer=True, is_writable=True)],
                data=memo_text.encode("utf-8"),
            )
            recent_blockhash = (await client.get_latest_blockhash()).value.blockhash
            message = Message.new_with_blockhash([instruction], self.keypair.pubkey(), recent_blockhash)
            transaction = Transaction([self.keypair], message, recent_blockhash)
            result = await client.send_transaction(transaction)
            signature = str(result.value)
            return EXPLORER_URL_TEMPLATE.format(signature=signature)
        finally:
            await client.close()
