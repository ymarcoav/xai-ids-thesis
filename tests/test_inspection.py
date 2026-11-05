import pandas as pd
import yaml

from xai_thesis.inspection import inspect_dataset_config


def test_inspect_dataset_config_writes_summary(tmp_path) -> None:
    raw_path = tmp_path / "raw"
    raw_path.mkdir()
    config_path = tmp_path / "dataset.yaml"
    output_path = tmp_path / "outputs"

    data = pd.DataFrame(
        {
            " feature ": [1.0, None, float("inf")],
            "Label": ["BENIGN", "Attack", "Attack"],
        }
    )
    data.to_csv(raw_path / "sample.csv", index=False)
    config_path.write_text(
        yaml.safe_dump(
            {
                "name": "sample",
                "raw_path": raw_path.as_posix(),
                "processed_path": "unused",
                "label_column": "label",
            }
        ),
        encoding="utf-8",
    )

    summary = inspect_dataset_config(config_path, output_path)

    assert summary["aggregate"]["rows_scanned"] == 3
    assert summary["files"][0]["label_column_found"] == "Label"
    assert summary["aggregate"]["label_counts"] == {"Attack": 2, "BENIGN": 1}
    assert summary["aggregate"]["columns_with_whitespace"] == [" feature "]
    assert summary["aggregate"]["numeric_columns_with_non_finite_values"] == [" feature "]
    assert (output_path / "sample" / "inspection.json").exists()
    assert (output_path / "sample" / "inspection.md").exists()


def test_inspect_dataset_config_uses_the_adapter_header_for_headerless_unsw_files(tmp_path) -> None:
    from xai_thesis.datasets.unsw_nb15 import UNSWNB15Dataset

    raw_path = tmp_path / "raw"
    raw_path.mkdir()
    columns = list(UNSWNB15Dataset.raw_column_names)
    rows = [["0"] * len(columns) for _ in range(2)]
    rows[0][columns.index("attack_cat")] = ""
    rows[1][columns.index("attack_cat")] = "Exploits"
    # The raw UNSW-NB15 files have no header row.
    pd.DataFrame(rows).to_csv(raw_path / "UNSW-NB15_1.csv", index=False, header=False)
    config_path = tmp_path / "unsw_nb15.yaml"
    config_path.write_text(
        yaml.safe_dump(
            {"name": "unsw_nb15", "raw_path": raw_path.as_posix(), "processed_path": "unused", "label_column": "attack_cat"}
        ),
        encoding="utf-8",
    )

    summary = inspect_dataset_config(config_path, tmp_path / "outputs")

    assert summary["aggregate"]["rows_scanned"] == 2
    assert summary["files"][0]["label_column_found"] == "attack_cat"
