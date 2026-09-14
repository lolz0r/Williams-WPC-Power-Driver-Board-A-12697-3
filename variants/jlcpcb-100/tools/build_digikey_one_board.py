#!/usr/bin/env python3
"""Build a one-board sourcing estimate from recorded public DigiKey facts.

No network access, cart changes, PCB edits, or qualification of substitutes.
"""
import csv
import hashlib
import json
import re
from collections import Counter, defaultdict
from decimal import Decimal, ROUND_HALF_UP
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RESEARCH = ROOT / "research/digikey-1"
OUT = ROOT / "output/digikey-1"
CENT = Decimal("0.01")


def read_csv(path):
    with path.open(newline="", encoding="utf-8-sig") as f:
        return list(csv.DictReader(f))


def write_csv(name, fields, rows):
    with (OUT / name).open("w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=fields, extrasaction="raise")
        writer.writeheader()
        writer.writerows(rows)


def money(amount):
    return str(amount.quantize(CENT, rounding=ROUND_HALF_UP))


def unique_text(values):
    return " | ".join(dict.fromkeys(v for v in values if v))


def crawl_text(record):
    match = re.search(r"Crawled: ([^;]+)", record.get("source_metadata", ""))
    return match.group(1) if match else "not reported"


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    source = read_csv(ROOT / "output/release-candidate/bom/all-components.csv")
    placements = read_csv(ROOT / "output/release-candidate/jlcpcb-assembly/placement-map.csv")
    catalog = json.loads((RESEARCH / "catalog.json").read_text())
    selection = json.loads((RESEARCH / "selection.json").read_text())
    source_hashes = json.loads((RESEARCH / "source-hashes.json").read_text())
    for name, digest in source_hashes.items():
        assert hashlib.sha256((ROOT / name).read_bytes()).hexdigest() == digest, name

    groups = defaultdict(list)
    place_groups = defaultdict(list)
    for row in source:
        groups[row["JLCPCB_part"] or row["Designator"]].append(row)
    for row in placements:
        place_groups[row["LCSC_part"]].append(row)
    assert len(place_groups) == 69
    assert len(placements) == 440
    assert len({p["Upload_designator"] for p in placements}) == 440
    assert set(selection) <= set(groups)

    bom, prices, reference_map = [], [], []
    required_electronics = 0
    for key, rows in groups.items():
        first = rows[0]
        dnp = all(r["DNP"] == "yes" for r in rows)
        assert len({r["MPN"] for r in rows}) == 1
        choice = selection.get(key, {"mpn": first["MPN"], "status": "exact"})
        status = "DNP_or_board_feature" if dnp else choice["status"]
        selected_mpn = "" if dnp else choice["mpn"] or ""
        record = catalog.get(selected_mpn)
        notes = choice.get("notes", "")
        if status == "candidate_parametric":
            notes = "Yageo RC0805 thick-film candidate: same resistance, +/-1%, 1/8W, 0805. Review working voltage, pulse loading and temperature coefficient. Quote only."
        if key in place_groups:
            positions = place_groups[key]
            required = sum(int(r["Quantity_per_board"]) for r in rows)
            assert required == len(positions), key
            required_electronics += required
            refs = " ".join(r["Upload_designator"] for r in positions)
            native = " ".join(dict.fromkeys(r["Native_reference"] for r in positions))
            assembly_types = {p["Assembly"] for p in positions}
            assembly = "SMT" if assembly_types == {"SMT"} else (
                "Fuse cartridge insertion" if assembly_types == {"Fuse cartridge insertion"} else "Through-hole soldered")
            category = "Electronics"
            assembly_notes = []
            for p in positions:
                note = p["Assembly_note"]
                if note and "CPL" not in note:
                    assembly_notes.append(p["Upload_designator"] + ": " + note)
            notes = unique_text([notes, *[r["Assembly_note"] for r in rows], *assembly_notes])
        else:
            refs = first["Designator"]
            native = first["Parent"]
            required = 0 if dnp else (1 if key == "THERMALPASTE" else int(first["Quantity_per_board"]))
            assembly = first["Assembly"]
            category = "Not purchased" if dnp else ("Consumable" if key == "THERMALPASTE" else "Hardware")
            if dnp:
                notes = first["Assembly_note"]
            elif key == "THERMALPASTE":
                notes = "One complete 3mL syringe charged as initial provision for this one-board build. Actual paste consumption is as needed; remaining paste is reusable. No batch spare allowance."
        needs_review = "yes" if status.startswith("candidate") or status == "unresolved" else "no"
        entry = {
            "Line": len(bom) + 1, "Group_ID": key, "Category": category,
            "Assembly": assembly, "References": refs, "Native_References": native,
            "Value_or_Description": unique_text(r["Value"] for r in rows), "Original_MPN": first["MPN"],
            "Original_Manufacturer": first["Manufacturer"], "Selected_MPN": selected_mpn,
            "Selected_Manufacturer": record["manufacturer"] if record else "",
            "DigiKey_Part_Number": record["sku"] if record else "",
            "Required_Qty_1_Board": required, "Purchase_Qty": "", "Surplus_Qty": "",
            "DNP": "yes" if dnp else "no", "Match_Status": status,
            "Engineering_Review_Required": needs_review, "Original_Footprint": unique_text(r["Footprint"] for r in rows),
            "Notes": notes, "Product_URL": record["url"].split("?")[0] if record else "",
        }
        bom.append(entry)
        for r in rows:
            reference_map.append({"Source_Designator": r["Designator"], "Parent": r["Parent"],
                                  "Source_Quantity": r["Quantity_per_board"], "BOM_Group_ID": key,
                                  "DNP": r["DNP"], "Selected_MPN": selected_mpn})

    cover = catalog["0853.0551"]
    bom.append({
        "Line": len(bom) + 1, "Group_ID": "FUSE_COVERS", "Category": "Added accessory",
        "Assembly": "Manual cover installation", "References": " ".join(p["Upload_designator"] + "_COVER" for p in place_groups["C268204"]),
        "Native_References": " ".join(dict.fromkeys(p["Native_reference"] for p in place_groups["C268204"])),
        "Value_or_Description": "Cover for SCHURTER OGN 5x20mm fuse block",
        "Original_MPN": "Included with FH1-200CK-G", "Original_Manufacturer": "HONGJU",
        "Selected_MPN": "0853.0551", "Selected_Manufacturer": cover["manufacturer"],
        "DigiKey_Part_Number": cover["sku"], "Required_Qty_1_Board": 15,
        "Purchase_Qty": "", "Surplus_Qty": "", "DNP": "no", "Match_Status": "candidate_accessory",
        "Engineering_Review_Required": "yes", "Original_Footprint": "Accessory; no independent PCB pads",
        "Notes": "One cover per selected 0031.8201 fuse block, including two empty holders. Original Hongju holder includes a cover. SCHURTER OGN drawing associates 0853.0551 with 0031.8201. Verify assembled cover envelope. https://media.digikey.com/pdf/Data%20Sheets/Schurter%20PDFs/DS_486_Fuseholders.pdf",
        "Product_URL": cover["url"],
    })

    assert required_electronics == 440
    for entry in bom:
        qty = entry["Required_Qty_1_Board"]
        if entry["DNP"] == "yes":
            entry.update(Purchase_Qty=0, Surplus_Qty=0)
            continue
        record = catalog.get(entry["Selected_MPN"])
        price = {"Row_Type": "ITEM", "Group_ID": entry["Group_ID"], "Category": entry["Category"],
                 "References": entry["References"], "Selected_MPN": entry["Selected_MPN"],
                 "DigiKey_Part_Number": entry["DigiKey_Part_Number"], "Board_Qty": 1,
                 "Required_Qty": qty, "Purchase_Qty": "", "Surplus_Qty": "",
                 "Minimum_Priced_Order_Qty": "", "Applied_Price_Break_Qty": "",
                 "Unit_Price_USD": "", "Required_Parts_Cost_USD": "", "Purchase_Cost_USD": "",
                 "Stock_Snapshot": "", "Stock_Covers_Purchase_Qty": "unknown",
                 "Match_Status": entry["Match_Status"], "Engineering_Review_Required": entry["Engineering_Review_Required"],
                 "Pricing_Status": "UNPRICED_UNRESOLVED", "Product_URL": entry["Product_URL"],
                 "Retrieved_UTC": "", "Source_Crawl_Age": "", "Notes": entry["Notes"]}
        if record:
            assert record["sku"] and record["manufacturer"] and record["prices"], entry
            assert re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9.,+/_-]*-ND", record["sku"]), record["sku"]
            # A page can list CT, reel and Digi-Reel prices. Use the first occurrence
            # of each quantity; CT precedes Digi-Reel when their tables are separate.
            tiers = {}
            for tier in record["prices"]:
                tiers.setdefault(tier["quantity"], Decimal(tier["unit_price_usd"]))
            minimum = min(tiers)
            buy = max(qty, minimum)
            applicable = max(t for t in tiers if t <= buy)
            unit = tiers[applicable]
            assert unit > 0 and minimum <= buy
            # Five fasteners have 100-piece minimum published price tiers.
            # Keep exact required quantities for every other part; no spares/discount overbuy.
            assert minimum == 1 or entry["Group_ID"] in {"M3X8", "M3X12", "M3NUT", "M4X20", "M4NUT"}
            if minimum > 1:
                assert minimum == 100 and buy % 100 == 0
                entry["Notes"] += " Purchase quantity uses the lowest published DigiKey price tier of 100 pieces; excess is retained stock, not a 100-board build."
            price.update(Purchase_Qty=buy, Surplus_Qty=buy-qty,
                         Minimum_Priced_Order_Qty=minimum, Applied_Price_Break_Qty=applicable,
                         Unit_Price_USD=str(unit), Required_Parts_Cost_USD=money(unit * qty),
                         Purchase_Cost_USD=money(unit * buy), Stock_Snapshot=record["stock"],
                         Stock_Covers_Purchase_Qty="yes" if record["stock"] is not None and record["stock"] >= buy else "no",
                         Pricing_Status="PUBLIC_PAGE_ESTIMATE", Retrieved_UTC=record["retrieved_utc"],
                         Source_Crawl_Age=crawl_text(record), Notes=entry["Notes"])
            entry.update(Purchase_Qty=buy, Surplus_Qty=buy-qty)
        prices.append(price)

    priced = [p for p in prices if p["Purchase_Cost_USD"]]
    unresolved = [p for p in prices if not p["Purchase_Cost_USD"]]
    shortfalls = [p for p in priced if p["Stock_Covers_Purchase_Qty"] != "yes"]
    purchase_total = sum((Decimal(p["Purchase_Cost_USD"]) for p in priced), Decimal(0))
    required_total = sum((Decimal(p["Required_Parts_Cost_USD"]) for p in priced), Decimal(0))
    totals = []
    for category in ["Electronics", "Hardware", "Consumable", "Added accessory"]:
        category_rows = [p for p in prices if p["Category"] == category]
        totals.append({"Metric": category + " priced subtotal", "Value": money(sum((Decimal(p["Purchase_Cost_USD"]) for p in category_rows if p["Purchase_Cost_USD"]), Decimal(0))),
                       "Unit": "USD", "Notes": f"{sum(bool(p['Purchase_Cost_USD']) for p in category_rows)} of {len(category_rows)} required lines priced; includes unqualified candidates."})
    totals.extend([
        {"Metric": "Board quantity", "Value": 1, "Unit": "board", "Notes": "No production spare allowance."},
        {"Metric": "Priced parts allocated to one board", "Value": money(required_total), "Unit": "USD", "Notes": "Required quantities valued at applied purchase-tier prices; includes one complete thermal-paste syringe and added covers; excludes unresolved fuse."},
        {"Metric": "Minimum-purchase excess cost", "Value": money(purchase_total-required_total), "Unit": "USD", "Notes": "Extra fasteners required to reach published minimum price tiers."},
        {"Metric": "Priced purchase subtotal", "Value": money(purchase_total), "Unit": "USD", "Notes": "Estimate including candidates and minimum purchases; excludes unresolved fuse."},
        {"Metric": "Required procurement lines", "Value": len(prices), "Unit": "lines", "Notes": "69 original electronic groups + 9 hardware/consumable groups + 1 added cover group."},
        {"Metric": "Priced procurement lines", "Value": len(priced), "Unit": "lines", "Notes": "Every priced line has DigiKey SKU, price tier, source URL and stock snapshot."},
        {"Metric": "Unpriced required lines", "Value": len(unresolved), "Unit": "lines", "Notes": "; ".join(p["References"] + ": " + p["Notes"] for p in unresolved)},
        {"Metric": "Priced stock shortfall lines", "Value": len(shortfalls), "Unit": "lines", "Notes": "Public cached snapshots; availability is not reserved."},
        {"Metric": "Lines requiring engineering review", "Value": sum(p["Engineering_Review_Required"] == "yes" for p in prices), "Unit": "lines", "Notes": "Candidates plus unresolved requirements; not qualified by the existing JLC variant's SPICE results."},
        {"Metric": "DNP or fabricated board features", "Value": sum(e["DNP"] == "yes" for e in bom), "Unit": "positions", "Notes": "Visible at zero purchase quantity in BOM; excluded from pricing."},
        {"Metric": "Final complete BOM total", "Value": "" if unresolved else money(purchase_total), "Unit": "USD", "Notes": "INCOMPLETE: F115 remains unpriced. Priced candidates also require engineering review." if unresolved else "Conditional estimate; candidates require engineering review."},
        {"Metric": "Excluded costs", "Value": "", "Unit": "", "Notes": "PCB fabrication, assembly labor, solder/process consumables other than specified thermal paste, freight, taxes, tariffs, fees and tooling."},
    ])
    for kind, required, purchase, status, note in [
        ("PRICED_SUBTOTAL", money(required_total), money(purchase_total), "PARTIAL_ESTIMATE", "Includes minimum purchase quantities and unqualified candidates; excludes F115."),
        ("FINAL_COMPLETE_BOM_TOTAL", "", "" if unresolved else money(purchase_total), "INCOMPLETE" if unresolved else "CONDITIONAL_ESTIMATE", "F115 0.75A ceramic time-delay fuse remains unresolved/unpriced. A complete board cost cannot yet be stated."),
    ]:
        summary = {k: "" for k in prices[0]}
        summary.update(Row_Type=kind, Board_Qty=1, Required_Parts_Cost_USD=required,
                       Purchase_Cost_USD=purchase, Pricing_Status=status, Notes=note)
        prices.append(summary)

    write_csv("DigiKey-BOM.csv", list(bom[0]), bom)
    write_csv("DigiKey-pricing.csv", list(prices[0]), prices)
    write_csv("DigiKey-totals.csv", ["Metric", "Value", "Unit", "Notes"], totals)
    write_csv("source-reference-coverage.csv", list(reference_map[0]), reference_map)
    assert len(reference_map) == len(source) == 471
    assert len({r["Source_Designator"] for r in reference_map}) == len(source)
    assert len(priced) + len(unresolved) == 79
    assert sum(p["Required_Qty"] for p in prices if p["Category"] == "Electronics") == 440
    assert sum(p["Required_Qty"] for p in prices if p["Category"] == "Hardware") == 30
    assert not shortfalls, shortfalls
    report = {"board_quantity": 1, "spares": 0, "source_rows_covered": len(reference_map),
              "electronic_purchase_units": 440, "assembly_units": dict(Counter(p["Assembly"] for p in placements)),
              "original_procurement_groups": 78, "added_cover_quantity": 15,
              "bom_rows": len(bom), "required_pricing_lines": len(priced)+len(unresolved),
              "priced_lines": len(priced), "unpriced_groups": [p["Group_ID"] for p in unresolved],
              "priced_purchase_subtotal_usd": money(purchase_total),
              "priced_required_parts_cost_usd": money(required_total),
              "final_complete_bom_total_usd": None if unresolved else money(purchase_total),
              "engineering_review_lines": sum(e["Engineering_Review_Required"] == "yes" for e in bom),
              "native_pcb_and_release_inputs_unchanged": True, "source_sha256": source_hashes,
              "validation": "PASS: coverage, quantities, stock snapshots, price tiers, positive prices and source hashes; NOT electrical/mechanical approval."}
    (OUT / "validation.json").write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
