# Đề xuất bổ sung và hoàn thiện thuật ngữ Bát Tự (Bazi Glossary Recommendations)

Tài liệu này tổng hợp các đề xuất bổ sung cấu trúc và định nghĩa thuật ngữ cho file `glossary.py` nhằm mục đích hoàn thiện 100% các quy luật cốt lõi trong luận đoán Bát Tự (Tứ Trụ).

## 1. Thiên Can (Heavenly Stems)

### Thiên Can Tương Khắc (天干相克 - Heavenly Stem Mutual Restraints)
Hiện tại hệ thống đã có "Lục Xung" (4 cặp Can tương xung: Giáp-Canh, Ất-Tân, Bính-Nhâm, Đinh-Quý) là xung đột mang tính chất vừa khắc vừa đẩy kịch liệt. Tuy nhiên, vẫn cần bổ sung khái niệm **Tương Khắc** (khắc chế thuần túy).
*   **Thuật ngữ:** Tương Khắc (相克 - Xiāng Kè - Mutual Restraint / Overcoming).
*   **Các cặp cần bổ sung:**
    *   Giáp khắc Mậu (甲克戊 - Jia restrains Wu)
    *   Ất khắc Kỷ (乙克己 - Yi restrains Ji)
    *   Mậu khắc Nhâm (戊克壬 - Wu restrains Ren)
    *   Kỷ khắc Quý (己克癸 - Ji restrains Gui)
    *   Nhâm khắc Bính (壬克丙 - Ren restrains Bing)
    *   Quý khắc Đinh (癸克丁 - Gui restrains Ding)
    *   Bính khắc Canh (丙克庚 - Bing restrains Geng)
    *   Đinh khắc Tân (丁克辛 - Ding restrains Xin)
    *   Canh khắc Giáp (庚克甲 - Geng restrains Jia) -> *Đã bao hàm trong Xung nhưng vẫn tính là Khắc*
    *   Tân khắc Ất (辛克乙 - Xin restrains Yi) -> *Đã bao hàm trong Xung nhưng vẫn tính là Khắc*

## 2. Địa Chi (Earthly Branches)

### 2.1. Ám Hợp (暗合 - Hidden Combinations)
Là sự kết hợp ngầm giữa các Địa Chi thông qua các Thiên Can tàng chứa bên trong (Tàng Can - 藏干). Rất quan trọng trong việc phán đoán những sự việc tiềm ẩn (tình cảm giấu giếm, tiền tài ngầm, v.v.).
*   **Thuật ngữ:** Ám Hợp (暗合 - Àn Hé - Hidden Combination).
*   **Các cặp tiêu biểu:**
    *   Dần - Sửu ám hợp (寅丑暗合 - Yin-Chou Hidden Combination): Giáp hợp Kỷ, Bính hợp Tân, Mậu hợp Quý.
    *   Mão - Thân ám hợp (卯申暗合 - Mao-Shen Hidden Combination): Ất hợp Canh.
    *   Ngọ - Hợi ám hợp (午亥暗合 - Wu-Hai Hidden Combination): Đinh hợp Nhâm, Kỷ hợp Giáp.

### 2.2. Củng Hợp / Bán Hợp Khuyết Vượng (拱合 - Arching Combinations)
Trong Tam Hợp Cục (VD: Dần - Ngọ - Tuất), cấu trúc lấy 2 chữ đầu và cuối (Sinh Địa + Mộ Địa) nhưng khuyết mất chữ giữa (Đế Vượng) gọi là Củng Hợp. Các Địa chi này có xu hướng "kéo" chữ ở giữa về, đợi Lưu niên/Đại vận lấp đầy để tạo thành Tam Hợp hoàn chỉnh.
*   **Thuật ngữ:** Củng Hợp / Ám Củng (拱合/暗拱 - Gǒng Hé / Àn Gǒng - Arching Combination).
*   **Các cặp bổ sung:**
    *   Dần - Tuất củng Hỏa (寅戌拱火 - Yin-Xu arches Fire)
    *   Hợi - Mùi củng Mộc (亥未拱木 - Hai-Wei arches Wood)
    *   Thân - Thìn củng Thủy (申辰拱水 - Shen-Chen arches Water)
    *   Tỵ - Sửu củng Kim (巳丑拱金 - Si-Chou arches Metal)

### 2.3. Hiệu chỉnh Lục Hợp Ngọ - Mùi (午未合)
Trong `glossary.py`, cặp Ngọ - Mùi được ấn định là `(Wu-Wei combine, transform to Fire - Ngọ Mùi hợp hóa Hỏa)`. Tuy nhiên, Ngọ và Mùi là Thái Âm - Thái Dương, có thể **Hóa Hỏa** (Hóa Thần = Fire) hoặc **Hóa Thổ** (Hóa Thần = Earth) tùy vào Nguyệt Lệnh và Can Dẫn Hóa. Cần nới lỏng hoặc tạo 2 định nghĩa cho cặp này để thuật toán xử lý linh hoạt hơn.

## 3. Nền tảng Can Chi (Rooting & Treasuries)

Đây là các trạng thái tĩnh đánh giá độ bền vững và sức mạnh thực tế của Ngũ Hành trong Mệnh bàn.

### 3.1. Thông Căn (通根 - Rooting)
Chỉ việc Thiên Can lộ trên mâm có gốc rễ (Tàng Can cùng loại) cắm tại các Địa Chi. Căn càng mạnh thì Can càng vững, không sợ bị Xung khắc.
*   **Thuật ngữ:** Thông Căn (通根 - Tōng Gēn - Rooting).
    *   Chính Căn / Bản Khí Căn (正根/本气根 - Main Qi Root): Ví dụ Giáp thông căn ở Dần/Mão.
    *   Dư Khí Căn / Tạp Khí Căn (余气根/杂气根 - Residual/Middle Qi Root).
    *   Hư Phù (虚浮 - Xū Fú - Vain and Floating / Unrooted): Thiên Can bồng bềnh không có rễ.

### 3.2. Mộ Khố (墓库 - Tombs and Treasuries)
Tứ Mộ Khố (Thìn, Tuất, Sửu, Mùi) chứa nguồn năng lượng cực kỳ phức tạp. Tùy thuộc vào trạng thái đóng mở mà nó là Mộ (chôn vùi) hay Khố (kho chứa).
*   **Thuật ngữ:** Mộ Khố (墓库 - Mù Kù - Tombs & Treasuries).
    *   Nhập Mộ (入墓 - Rù Mù - Entering the Tomb): Yếu tố bị nhốt lại, mất khả năng tác dụng.
    *   Nhập Khố (入库 - Rù Kù - Entering the Treasury): Yếu tố được cất giữ, tích lũy.
    *   Mở Khố / Xung Khố (开库 / 冲库 - Kāi Kù / Chōng Kù - Opening the Treasury): Nhờ bị Xung/Hình (VD: Thìn Tuất xung) làm bật nắp kho, xuất tàng can ra ngoài để sử dụng làm Dụng thần.

## 4. Trạng Thái Trống Rỗng (Emptiness)

### Tuần Không / Không Vong (旬空 / 空亡 - Emptiness)
Khái niệm bắt nguồn từ 60 Hoa Giáp, do có 10 Can kết hợp 12 Chi nên dư ra 2 Chi không có Can ghép cùng tạo thành sự "Trống rỗng" (Không Vong). Không Vong có khả năng **hủy bỏ sức mạnh** của Thần sát, giải trừ Hợp hóa và làm suy yếu lực Xung khắc. Vị trí này có thể nằm trong `symbols/stars` tuy nhiên nó hoạt động như một hàm Interaction độc lập trong mọi hệ tư tưởng Bát Tự.
*   **Thuật ngữ:**
    *   Không Vong / Tuần Không (空亡 / 旬空 - Kōng Wáng / Xún Kōng - Death and Emptiness).
    *   Triệt Không (截空 - Jié Kōng - Intercepting Emptiness).
    *   Giải Không (解空 - Jiě Kōng - Resolving Emptiness): Khi Địa Chi Không Vong gặp Xung, Hợp, Hình từ đại vận/lưu niên sẽ được lấp đầy.

## 5. Cung Vị, Trụ & Nguyên Cục (Palaces & Pillars)

Để chuẩn hóa đầu vào (Input) và giải thích Đầu ra (Output) trong các Report, nên bổ sung nhóm thuật ngữ mô tả vị trí định vị.

*   Thuật ngữ Tứ Trụ Cung (四柱宫位 - Four Pillars Palaces):
    *   Niên Cung / Cung Tổ Tiên (年宫 / 祖辈宫 - Nián Gōng - Year Palace / Ancestor Palace).
    *   Nguyệt Cung / Cung Phụ Mẫu (月宫 / 父母宫 - Yuè Gōng - Month Palace / Parents Palace).
    *   Nhật Cung / Cung Phu Thê (日宫 / 夫妻宫 - Rì Gōng - Day Palace / Spouse Palace).
    *   Thời Cung / Cung Tử Tức (时宫 / 子女宫 - Shí Gōng - Hour Palace / Children Palace).

*   Các trụ mở rộng (thường lấy từ hệ Tử Vi sang phối hợp cùng Bát tự):
    *   Thai Nguyên (胎元 - Tāi Yuán - Conception Pillar).
    *   Mệnh Cung / Cung Mệnh (命宫 - Mìng Gōng - Life Palace).
    *   Thân Cung / Cung Thân (身宫 - Shēn Gōng - Body Palace).
