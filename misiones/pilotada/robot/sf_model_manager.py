#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import json
import os
import re
import shutil
import tempfile
import time
import uuid
import zipfile
from pathlib import Path


DEFAULT_MODELS_DIR = Path(
    "/home/pi/robot_custom/modelos"
)

DEFAULT_TRASH_DIR = Path(
    "/home/pi/safevision_backups/model_trash"
)

MODEL_EXTENSIONS = (
    ".pt",
    ".weights",
    ".torchscript",
)

ASSOCIATED_EXTENSIONS = (
    ".pt",
    ".weights",
    ".torchscript",
    ".json",
)

PRIMARY_PRIORITY = (
    ".pt",
    ".weights",
    ".torchscript",
)

NAME_RE = re.compile(
    r"^[A-Za-z0-9][A-Za-z0-9._-]{0,127}$"
)


class ModelManagerError(Exception):
    pass


class ModelNotFound(ModelManagerError):
    pass


class ModelConflict(ModelManagerError):
    pass


class InvalidModel(ModelManagerError):
    pass


class ModelManager:
    def __init__(
        self,
        models_dir=DEFAULT_MODELS_DIR,
        trash_dir=DEFAULT_TRASH_DIR
    ):
        self.models_dir = Path(
            models_dir
        )

        self.trash_dir = Path(
            trash_dir
        )

        self.models_dir.mkdir(
            parents=True,
            exist_ok=True
        )

    def _stem(self, value):
        if not isinstance(
            value,
            str
        ):
            raise InvalidModel(
                "Nombre de modelo invalido."
            )

        name = value.strip()

        suffix = Path(
            name
        ).suffix.lower()

        if suffix in ASSOCIATED_EXTENSIONS:
            name = Path(
                name
            ).stem

        if (
            not name
            or
            not NAME_RE.fullmatch(
                name
            )
        ):
            raise InvalidModel(
                (
                    "Nombre invalido. Usa letras, "
                    "numeros, punto, guion o guion bajo."
                )
            )

        return name

    def _artifacts(self, stem):
        stem = self._stem(
            stem
        )

        result = {}

        for extension in ASSOCIATED_EXTENSIONS:
            path = (
                self.models_dir
                /
                (
                    stem
                    +
                    extension
                )
            )

            if path.is_file():
                result[
                    extension
                ] = path

        return result

    def _metadata(self, path):
        try:
            with path.open(
                "r",
                encoding="utf-8"
            ) as file:
                data = json.load(
                    file
                )

            if not isinstance(
                data,
                dict
            ):
                return {}, (
                    "JSON no contiene un objeto."
                )

            return data, None

        except Exception as exc:
            return {}, str(
                exc
            )

    def _record(self, stem):
        artifacts = self._artifacts(
            stem
        )

        if not any(
            extension in artifacts
            for extension
            in MODEL_EXTENSIONS
        ):
            raise ModelNotFound(
                "Modelo no encontrado."
            )

        primary = None

        for extension in PRIMARY_PRIORITY:
            if extension in artifacts:
                primary = extension
                break

        metadata = {}
        metadata_error = None

        if ".json" in artifacts:
            metadata, metadata_error = (
                self._metadata(
                    artifacts[
                        ".json"
                    ]
                )
            )

        classes = metadata.get(
            "clases",
            []
        )

        if not isinstance(
            classes,
            list
        ):
            classes = []

        items = []
        total = 0

        for extension in ASSOCIATED_EXTENSIONS:
            path = artifacts.get(
                extension
            )

            if path is None:
                continue

            size = path.stat().st_size
            total += size

            items.append({
                "name": path.name,
                "extension": extension,
                "bytes": size,
                "mb": round(
                    size
                    /
                    (1024.0 * 1024.0),
                    3
                )
            })

        return {
            "name": stem,
            "display_name": str(
                metadata.get(
                    "nombre_modelo",
                    stem
                )
            ),
            "version": metadata.get(
                "version"
            ),
            "classes": [
                str(item)
                for item in classes
            ],
            "class_count": len(
                classes
            ),
            "metadata": metadata,
            "metadata_error": (
                metadata_error
            ),
            "primary": (
                artifacts[
                    primary
                ].name
                if primary
                else None
            ),
            "primary_extension": (
                primary
            ),
            "activatable": (
                primary == ".pt"
            ),
            "artifacts": items,
            "bytes": total,
            "mb": round(
                total
                /
                (1024.0 * 1024.0),
                3
            )
        }

    def list_models(self):
        stems = set()

        for path in self.models_dir.iterdir():
            if (
                path.is_file()
                and
                path.suffix.lower()
                in MODEL_EXTENSIONS
            ):
                stems.add(
                    path.stem
                )

        return [
            self._record(
                stem
            )
            for stem in sorted(
                stems,
                key=lambda value: (
                    value.lower()
                )
            )
        ]

    def get(self, name):
        return self._record(
            self._stem(
                name
            )
        )

    def artifact_path(
        self,
        name,
        extension
    ):
        stem = self._stem(
            name
        )

        ext = str(
            extension
        ).strip().lower()

        if not ext.startswith(
            "."
        ):
            ext = "." + ext

        if ext not in ASSOCIATED_EXTENSIONS:
            raise InvalidModel(
                "Artefacto no permitido."
            )

        path = (
            self.models_dir
            /
            (
                stem
                +
                ext
            )
        )

        if not path.is_file():
            raise ModelNotFound(
                "Artefacto no encontrado."
            )

        return path

    def update_metadata(
        self,
        name,
        data
    ):
        stem = self._stem(
            name
        )

        self._record(
            stem
        )

        if not isinstance(
            data,
            dict
        ):
            raise InvalidModel(
                "Metadatos invalidos."
            )

        result = dict(
            data
        )

        classes = result.get(
            "clases",
            []
        )

        if not isinstance(
            classes,
            list
        ):
            raise InvalidModel(
                "'clases' debe ser una lista."
            )

        clean = []

        for item in classes:
            value = str(
                item
            ).strip()

            if not value:
                continue

            if len(
                value
            ) > 128:
                raise InvalidModel(
                    "Clase demasiado larga."
                )

            clean.append(
                value
            )

        result[
            "clases"
        ] = clean

        if "nombre_modelo" in result:
            result[
                "nombre_modelo"
            ] = str(
                result[
                    "nombre_modelo"
                ]
            ).strip()

        if "version" in result:
            result[
                "version"
            ] = str(
                result[
                    "version"
                ]
            ).strip()

        path = (
            self.models_dir
            /
            (
                stem
                +
                ".json"
            )
        )

        tmp = (
            self.models_dir
            /
            (
                ".{}.{}.tmp".format(
                    stem,
                    uuid.uuid4().hex
                )
            )
        )

        try:
            with tmp.open(
                "w",
                encoding="utf-8"
            ) as file:
                json.dump(
                    result,
                    file,
                    ensure_ascii=False,
                    indent=2,
                    sort_keys=True
                )

                file.write(
                    "\n"
                )

            os.replace(
                str(tmp),
                str(path)
            )

        finally:
            if tmp.exists():
                tmp.unlink()

        return self._record(
            stem
        )

    def rename(
        self,
        old_name,
        new_name
    ):
        old_stem = self._stem(
            old_name
        )

        new_stem = self._stem(
            new_name
        )

        if old_stem == new_stem:
            return self._record(
                old_stem
            )

        artifacts = self._artifacts(
            old_stem
        )

        if not any(
            extension in artifacts
            for extension
            in MODEL_EXTENSIONS
        ):
            raise ModelNotFound(
                "Modelo no encontrado."
            )

        pairs = []

        for extension in ASSOCIATED_EXTENSIONS:
            source = artifacts.get(
                extension
            )

            if source is None:
                continue

            target = (
                self.models_dir
                /
                (
                    new_stem
                    +
                    extension
                )
            )

            if target.exists():
                raise ModelConflict(
                    (
                        "Ya existe {}."
                    ).format(
                        target.name
                    )
                )

            pairs.append(
                (
                    source,
                    target
                )
            )

        moved = []

        try:
            for source, target in pairs:
                os.rename(
                    str(source),
                    str(target)
                )

                moved.append(
                    (
                        target,
                        source
                    )
                )

        except Exception:
            for current, original in reversed(
                moved
            ):
                if (
                    current.exists()
                    and
                    not original.exists()
                ):
                    os.rename(
                        str(current),
                        str(original)
                    )

            raise

        return self._record(
            new_stem
        )

    def delete(self, name):
        stem = self._stem(
            name
        )

        artifacts = self._artifacts(
            stem
        )

        if not any(
            extension in artifacts
            for extension
            in MODEL_EXTENSIONS
        ):
            raise ModelNotFound(
                "Modelo no encontrado."
            )

        stamp = time.strftime(
            "%Y%m%d_%H%M%S"
        )

        destination = (
            self.trash_dir
            /
            (
                "{}_{}".format(
                    stamp,
                    stem
                )
            )
        )

        counter = 1

        while destination.exists():
            destination = (
                self.trash_dir
                /
                (
                    "{}_{}_{}".format(
                        stamp,
                        stem,
                        counter
                    )
                )
            )

            counter += 1

        destination.mkdir(
            parents=True,
            exist_ok=False
        )

        files = []

        for extension in ASSOCIATED_EXTENSIONS:
            path = artifacts.get(
                extension
            )

            if path is None:
                continue

            target = (
                destination
                /
                path.name
            )

            shutil.move(
                str(path),
                str(target)
            )

            files.append(
                target.name
            )

        return {
            "name": stem,
            "files": files,
            "backup": str(
                destination
            )
        }

    def _unique_import_stem(
        self,
        requested,
        extensions
    ):
        stem = self._stem(
            requested
        )

        def collides(candidate):
            return any(
                (
                    self.models_dir
                    /
                    (
                        candidate
                        +
                        extension
                    )
                ).exists()
                for extension
                in extensions
            )

        if not collides(
            stem
        ):
            return stem

        stamp = time.strftime(
            "%Y%m%d_%H%M%S"
        )

        base = (
            "{}_{}".format(
                stem,
                stamp
            )
        )

        candidate = base
        index = 1

        while collides(
            candidate
        ):
            candidate = (
                "{}_{}".format(
                    base,
                    index
                )
            )

            index += 1

        return candidate

    def import_zip(
        self,
        fileobj
    ):
        try:
            archive = zipfile.ZipFile(
                fileobj,
                "r"
            )

        except Exception:
            raise InvalidModel(
                "ZIP invalido o corrupto."
            )

        imported = []

        with archive:
            infos = [
                info
                for info in archive.infolist()
                if not info.is_dir()
            ]

            if (
                not infos
                or
                len(infos) > 64
            ):
                raise InvalidModel(
                    "Contenido ZIP invalido."
                )

            grouped = {}

            for info in infos:
                raw = info.filename

                if (
                    "/" in raw
                    or
                    "\\" in raw
                ):
                    raise InvalidModel(
                        (
                            "El ZIP debe ser plano, "
                            "sin carpetas."
                        )
                    )

                path = Path(
                    raw
                )

                extension = (
                    path.suffix.lower()
                )

                if extension not in ASSOCIATED_EXTENSIONS:
                    continue

                stem = self._stem(
                    path.stem
                )

                group = grouped.setdefault(
                    stem,
                    {}
                )

                if extension in group:
                    raise InvalidModel(
                        (
                            "Artefacto duplicado: "
                            "{}{}"
                        ).format(
                            stem,
                            extension
                        )
                    )

                group[
                    extension
                ] = info

            groups = {
                stem: files
                for stem, files
                in grouped.items()
                if any(
                    extension in files
                    for extension
                    in MODEL_EXTENSIONS
                )
            }

            if not groups:
                raise InvalidModel(
                    (
                        "No se encontro modelo "
                        ".pt/.weights/.torchscript."
                    )
                )

            staging = Path(
                tempfile.mkdtemp(
                    prefix=(
                        "safevision_model_import_"
                    )
                )
            )

            try:
                for requested, files in (
                    groups.items()
                ):
                    stem = (
                        self._unique_import_stem(
                            requested,
                            files.keys()
                        )
                    )

                    prepared = []

                    for extension, info in (
                        files.items()
                    ):
                        temp_path = (
                            staging
                            /
                            (
                                stem
                                +
                                extension
                            )
                        )

                        with archive.open(
                            info,
                            "r"
                        ) as source:
                            with temp_path.open(
                                "wb"
                            ) as target:
                                shutil.copyfileobj(
                                    source,
                                    target,
                                    length=(
                                        1024 * 1024
                                    )
                                )

                        prepared.append(
                            (
                                extension,
                                temp_path
                            )
                        )

                    for extension, temp_path in (
                        prepared
                    ):
                        target = (
                            self.models_dir
                            /
                            (
                                stem
                                +
                                extension
                            )
                        )

                        os.replace(
                            str(temp_path),
                            str(target)
                        )

                    imported.append(
                        self._record(
                            stem
                        )
                    )

            finally:
                shutil.rmtree(
                    str(staging),
                    ignore_errors=True
                )

        return imported

    def export_to_temp(
        self,
        name
    ):
        record = self.get(
            name
        )

        stem = record[
            "name"
        ]

        artifacts = self._artifacts(
            stem
        )

        temp = tempfile.NamedTemporaryFile(
            prefix=(
                "safevision_{}_".format(
                    stem
                )
            ),
            suffix=".zip",
            delete=False
        )

        temp_path = Path(
            temp.name
        )

        temp.close()

        try:
            with zipfile.ZipFile(
                str(temp_path),
                "w",
                zipfile.ZIP_DEFLATED
            ) as archive:
                for extension in ASSOCIATED_EXTENSIONS:
                    path = artifacts.get(
                        extension
                    )

                    if path is None:
                        continue

                    archive.write(
                        str(path),
                        arcname=path.name
                    )

        except Exception:
            if temp_path.exists():
                temp_path.unlink()

            raise

        return temp_path
