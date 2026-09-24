"""Histórico reversível de correções na sessão."""

from core.constants import FIELDS
from core.models import Patch, PatchOrigin, Record


class PatchLog:
    """Aplica correções em memória e desfaz o último grupo inteiro."""

    def __init__(self) -> None:
        self.patches: list[Patch] = []
        self._seq = 0
        self._group = 0

    def new_group(self) -> int:
        """Reserva um identificador para uma ação com vários patches."""
        self._group += 1
        return self._group

    def _append(
        self,
        rec: Record,
        field: str | None,
        old: str | None,
        new: str | None,
        origin: PatchOrigin,
        group: int | None,
    ) -> Patch:
        self._seq += 1
        patch = Patch(
            self._seq,
            group if group is not None else self.new_group(),
            rec.id,
            field,
            old,
            new,
            origin,
        )
        self.patches.append(patch)
        return patch

    def set_value(
        self,
        rec: Record,
        field: str,
        new: str,
        origin: PatchOrigin,
        group: int | None = None,
    ) -> Patch | None:
        """Altera um campo de texto ou retorna None se não houver mudança."""
        if field not in FIELDS:
            raise ValueError("campo inválido")
        old = rec.input[field]
        if new == old:
            return None
        rec.input[field] = new
        return self._append(rec, field, old, new, origin, group)

    def delete(self, rec: Record, group: int | None = None) -> Patch:
        """Marca registro como excluído sem removê-lo da memória."""
        if rec.deleted:
            raise ValueError("registro já excluído")
        rec.deleted = True
        return self._append(rec, None, None, None, PatchOrigin.EXCLUSAO, group)

    def restore(self, rec: Record) -> Patch:
        """Restaura um registro excluído."""
        if not rec.deleted:
            raise ValueError("registro não excluído")
        rec.deleted = False
        return self._append(rec, None, None, None, PatchOrigin.RESTAURACAO, None)

    def undo_last(self, records_by_id: dict[int, Record]) -> list[Patch]:
        """Desfaz em ordem reversa todos os patches do último grupo."""
        if not self.patches:
            return []
        group = self.patches[-1].group
        undone: list[Patch] = []
        while self.patches and self.patches[-1].group == group:
            patch = self.patches.pop()
            record = records_by_id.get(patch.record_id)
            if record is not None:
                if patch.origin == PatchOrigin.EXCLUSAO:
                    record.deleted = False
                elif patch.origin == PatchOrigin.RESTAURACAO:
                    record.deleted = True
                elif patch.field is not None and patch.old is not None:
                    record.input[patch.field] = patch.old
            undone.append(patch)
        return undone

    def drop_records(self, record_ids: set[int]) -> None:
        """Descarta correções de registros removidos da carga."""
        self.patches = [patch for patch in self.patches if patch.record_id not in record_ids]

    def can_undo(self) -> bool:
        """Indica se há ação reversível."""
        return bool(self.patches)
