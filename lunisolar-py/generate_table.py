import json
import os

stems = ["Giáp", "Ất", "Bính", "Đinh", "Mậu", "Kỷ", "Canh", "Tân", "Nhâm", "Quý"]
branches = ["Tý", "Sửu", "Dần", "Mão", "Thìn", "Tỵ", "Ngọ", "Mùi", "Thân", "Dậu", "Tuất", "Hợi"]

stem_elements = {
    "Giáp": "Mộc", "Ất": "Mộc", 
    "Bính": "Hỏa", "Đinh": "Hỏa", 
    "Mậu": "Thổ", "Kỷ": "Thổ", 
    "Canh": "Kim", "Tân": "Kim", 
    "Nhâm": "Thủy", "Quý": "Thủy"
}

taixuan_stems = {
    "Giáp": 9, "Kỷ": 9,
    "Ất": 8, "Canh": 8,
    "Bính": 7, "Tân": 7,
    "Đinh": 6, "Nhâm": 6,
    "Mậu": 5, "Quý": 5
}
taixuan_branches = {
    "Tý": 9, "Ngọ": 9,
    "Sửu": 8, "Mùi": 8,
    "Dần": 7, "Thân": 7,
    "Mão": 6, "Dậu": 6,
    "Thìn": 5, "Tuất": 5,
    "Tỵ": 4, "Hợi": 4
}

hado = {
    1: "Thủy", 6: "Thủy",
    2: "Hỏa", 7: "Hỏa",
    3: "Mộc", 8: "Mộc",
    4: "Kim", 9: "Kim",
    5: "Thổ", 10: "Thổ",
    0: "Thổ"
}

sheng = {
    "Thủy": "Mộc",
    "Mộc": "Hỏa",
    "Hỏa": "Thổ",
    "Thổ": "Kim",
    "Kim": "Thủy"
}

chang_sheng_stages = [
    "Trường Sinh", "Mộc Dục", "Quan Đới", "Lâm Quan", "Đế Vượng", "Suy",
    "Bệnh", "Tử", "Mộ", "Tuyệt", "Thai", "Dưỡng"
]

def get_chang_sheng(stem, branch):
    # Element of stem
    elem = stem_elements[stem]
    is_yang = stems.index(stem) % 2 == 0
    if elem == "Mộc":
        start = branches.index("Hợi")
    elif elem == "Hỏa" or elem == "Thổ":
        start = branches.index("Dần")
    elif elem == "Kim":
        start = branches.index("Tỵ")
    elif elem == "Thủy":
        start = branches.index("Thân")

    if not is_yang:
        # Yin stems: go backward, start offset +1 from yang's Mộc Dục (so +1 position relative to yang start, Wait:
        # Giáp (Mộc) TS tại Hợi, Mộc Dục tại Tý. Ất (Mộc âm) TS tại Ngọ (Mộc Dục của nó ngược lại).
        # Standard rules for Yin Stems:
        # Ất (Yin Wood): Trường Sinh at Ngọ
        # Đinh/Kỷ (Yin Fire/Earth): Trường Sinh at Dậu
        # Tân (Yin Metal): Trường Sinh at Tý
        # Quý (Yin Water): Trường Sinh at Mão
        if elem == "Mộc": start = branches.index("Ngọ")
        elif elem == "Hỏa" or elem == "Thổ": start = branches.index("Dậu")
        elif elem == "Kim": start = branches.index("Tý")
        elif elem == "Thủy": start = branches.index("Mão")

    target = branches.index(branch)
    if is_yang:
        idx = (target - start) % 12
    else:
        idx = (start - target) % 12
    return chang_sheng_stages[idx]

hidden_stems = {
    "Tý": [("Quý", "chính")],
    "Sửu": [("Kỷ", "chính"), ("Tân", "trung"), ("Quý", "dư")],
    "Dần": [("Giáp", "chính"), ("Bính", "trung"), ("Mậu", "dư")],
    "Mão": [("Ất", "chính")],
    "Thìn": [("Mậu", "chính"), ("Quý", "trung"), ("Ất", "dư")],
    "Tỵ": [("Bính", "chính"), ("Canh", "trung"), ("Mậu", "dư")],
    "Ngọ": [("Đinh", "chính"), ("Kỷ", "trung")],
    "Mùi": [("Kỷ", "chính"), ("Đinh", "trung"), ("Ất", "dư")],
    "Thân": [("Canh", "chính"), ("Nhâm", "trung"), ("Mậu", "dư")],
    "Dậu": [("Tân", "chính")],
    "Tuất": [("Mậu", "chính"), ("Đinh", "trung"), ("Tân", "dư")],
    "Hợi": [("Nhâm", "chính"), ("Giáp", "trung")]
}

nayin_names = [
    "Hải Trung Kim", "Lư Trung Hỏa", "Đại Lâm Mộc", "Lộ Bàng Thổ", "Kiếm Phong Kim", "Sơn Đầu Hỏa",
    "Giản Hạ Thủy", "Thành Đầu Thổ", "Bạch Lạp Kim", "Dương Liễu Mộc", "Tuyền Trung Thủy", "Ốc Thượng Thổ",
    "Tích Lịch Hỏa", "Tùng Bách Mộc", "Trường Lưu Thủy", "Sa Trung Kim", "Sơn Hạ Hỏa", "Bình Địa Mộc",
    "Bích Thượng Thổ", "Kim Bạch Kim", "Phúc Đăng Hỏa", "Thiên Hà Thủy", "Đại Trạch Thổ", "Thoa Xuyến Kim",
    "Tang Đố Mộc", "Đại Khê Thủy", "Sa Trung Thổ", "Thiên Thượng Hỏa", "Thạch Lựu Mộc", "Đại Hải Thủy"
]

rows = []
for i in range(30):
    s1 = stems[(i * 2) % 10]
    b1 = branches[(i * 2) % 12]
    s2 = stems[(i * 2 + 1) % 10]
    b2 = branches[(i * 2 + 1) % 12]
    
    name_pair = f"{s1} {b1} + {s2} {b2}"
    t1, tb1, t2, tb2 = taixuan_stems[s1], taixuan_branches[b1], taixuan_stems[s2], taixuan_branches[b2]
    sumS = t1 + tb1 + t2 + tb2
    S_str = f"{t1} + {tb1} + {t2} + {tb2} = {sumS}"
    
    X = 49 - sumS
    
    sum_digits = sum(int(d) for d in str(X))
    if sum_digits > 10:
        Y = sum_digits % 5
        Y_str = f"X={X} -> Y= {sum_digits} (vì > 10 lấy dư 5) = {Y}"
    else:
        Y = sum_digits
        Y_str = f"X={X} -> Y={Y}"
    
    Y_elem = hado.get(Y, "Thủy") # Fallback to Thủy if somehow 0
    
    Z = X % 5
    Z_val = 5 if Z == 0 else Z
    Z_str = f"X % 5 = {Z}" + (" -> 5" if Z == 0 else "")
    
    Z_elem = hado[Z_val]
    nayin_elem = sheng[Z_elem]
    nayin_name = nayin_names[i]
    
    def format_tc_10(s, b):
        return f"{s} ({stem_elements[s]}) tại {b}: {get_chang_sheng(s, b)}"
    tc10_1 = format_tc_10(s1, b1)
    tc10_2 = format_tc_10(s2, b2)
    col10 = f"Năm 1: {tc10_1}<br>Năm 2: {tc10_2}"
    
    def format_chinh(s, b):
        hs = hidden_stems[b]
        chinh = next((h for h in hs if h[1] == "chính"), None)
        if chinh:
            return f"Tại {b} tàng {chinh[0]} (chính - {stem_elements[chinh[0]]}): {get_chang_sheng(chinh[0], b)}"
        return f"Tại {b} không có chính"
        
    col11 = f"Năm 1: {format_chinh(s1, b1)}<br>Năm 2: {format_chinh(s2, b2)}"
    
    def format_phu(s, b):
        hs = hidden_stems[b]
        phu = [h for h in hs if h[1] != "chính"]
        if not phu:
            return f"Tại {b} không có trung/dư"
        parts = [f"{h[0]} ({h[1]} - {stem_elements[h[0]]}): {get_chang_sheng(h[0], b)}" for h in phu]
        return f"Tại {b} tàng " + ", ".join(parts)
        
    col12 = f"Năm 1: {format_phu(s1, b1)}<br>Năm 2: {format_phu(s2, b2)}"
    
    rows.append([
        name_pair, S_str, str(X), Y_str, Y_elem, Z_str, Z_elem, nayin_elem, nayin_name,
        col10, col11, col12
    ])

with open("c:/Users/Huy/Downloads/code/lunisolar-ts/.contexts/0004_taixuan_shu_nayin.md", "w", encoding="utf-8") as f:
    f.write("# Tính Ngũ Hành Nạp Âm từ Thái Huyền Số\n\n")
    f.write("Dưới đây là bảng tính Ngũ Hành Nạp Âm cho 60 Hoa Giáp sử dụng Thái Huyền Số và Đại Diễn Số (49).\n\n")
    
    f.write("## Nguyên lý tính\n")
    f.write("1. **Thái Huyền Số thiên can**: Giáp/Kỷ = 9, Ất/Canh = 8, Bính/Tân = 7, Đinh/Nhâm = 6, Mậu/Quý = 5.\n")
    f.write("2. **Thái Huyền Số địa chi**: Tý/Ngọ = 9, Sửu/Mùi = 8, Dần/Thân = 7, Mão/Dậu = 6, Thìn/Tuất = 5, Tỵ/Hợi = 4.\n")
    f.write("3. Lấy 2 năm liền kề (Ví dụ: Giáp Tý + Ất Sửu), tính tổng giá trị của 2 can và 2 chi, gọi là `S`.\n")
    f.write("4. Đại Diễn số là 50, dùng 49 để tính (trừ 1 thái cực). `X = 49 - S`.\n")
    f.write("5. Tính `Z = X % 5`. Nếu `Z = 0` thì cho `Z = 5`.\n")
    f.write("6. Tra số `Z` vào ngũ hành của **Hà Đồ** để tìm Ngũ Hành Gốc: 1 = Thủy, 2 = Hỏa, 3 = Mộc, 4 = Kim, 5 = Thổ.\n")
    f.write("7. Hành Nạp Âm là hành được sinh ra từ Hành Gốc (Gốc sinh Nạp Âm). Ví dụ: Gốc là Thổ -> sinh Kim -> Nạp âm Kim.\n")
    f.write("8. Ngũ hành sinh: Thủy sinh Mộc, Mộc sinh Hỏa, Hỏa sinh Thổ, Thổ sinh Kim, Kim sinh Thủy.\n\n")

    f.write("## Bảng Tính Cho 60 Hoa Giáp\n\n")
    headers = ["Năm", "S (Tổng)", "X (49-S)", "Y (Tổng chữ số X)", "Hành Hà Đồ Y", "Z (X % 5)", "Hành Gốc Z", "Hành Nạp Âm", "Tên Nạp Âm", "Can / Chi (Vòng Trường Sinh)", "Tàng Can Chính / Chi", "Tàng Can Trung, Dư / Chi"]
    f.write("| " + " | ".join(headers) + " |\n")
    f.write("|" + "|".join(["---"] * len(headers)) + "|\n")
    
    for r in rows:
        f.write("| " + " | ".join(r) + " |\n")

print("Done generating markdown file")
