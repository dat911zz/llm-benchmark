"""Question Bank: 45 hardcoded questions across 8 categories."""

from llm_bench.models import Question

# ── Question Bank ─────────────────────────────────────────────────────────────
# 45 questions: 8 categories × (2 Easy + 3 Medium + 2 Hard) ≈ balanced
# EN / VI roughly 50/50

QUESTIONS: list[Question] = [

    # ════════════════════════════════════════════════════════
    # CATEGORY 1: LOGIC & DEDUCTIVE REASONING
    # ════════════════════════════════════════════════════════

    Question(
        id="L-E1", category="Logic", lang="en", difficulty="Easy",
        prompt=(
            "All birds have wings. Penguins are birds. "
            "Do penguins have wings? Answer YES or NO, then explain in one sentence."
        ),
        reference="Yes, penguins have wings (even though they cannot fly).",
        keywords=["yes"],
        any_keywords=["wing", "penguin", "bird"],
        any_min=2,
        max_tokens=150,
    ),

    Question(
        id="L-E2", category="Logic", lang="vi", difficulty="Easy",
        prompt=(
            "Tat ca nguoi Viet Nam deu song o Trai Dat. "
            "Nam la nguoi Viet Nam. "
            "Nam co song o Trai Dat khong? Tra loi CO hoac KHONG va giai thich mot cau."
        ),
        reference="Co, Nam song o Trai Dat (syllogism don gian).",
        keywords=["co"],
        any_keywords=["trai dat", "viet nam", "nam"],
        any_min=2,
        max_tokens=150,
    ),

    Question(
        id="L-M1", category="Logic", lang="en", difficulty="Medium",
        prompt=(
            "A bat and a ball cost $1.10 in total. "
            "The bat costs $1.00 more than the ball. "
            "How much does the ball cost? Show your working step by step."
        ),
        reference="Ball = $0.05 (5 cents). Let ball=x, bat=x+1.00; x+(x+1.00)=1.10 → 2x=0.10 → x=0.05.",
        exact_numbers=["0.05", "5"],
        any_keywords=["cent", "dollar", "ball"],
        any_min=1,
        max_tokens=300,
    ),

    Question(
        id="L-M2", category="Logic", lang="vi", difficulty="Medium",
        prompt=(
            "Co 3 hop: mot hop chi co tao, mot hop chi co cam, mot hop co ca hai. "
            "TAT CA nhan dan tren hop deu SAI. "
            "Ban chi duoc lay 1 qua tu 1 hop. Ban chon hop nao de dat lai nhan dung cho ca 3 hop? "
            "Giai thich buoc buoc."
        ),
        reference=(
            "Chon hop co nhan 'Ca hai'. Vi nhan sai, hop do phai la chi tao hoac chi cam. "
            "Qua ban lay se xac dinh hop do. Tu do suy ra 2 hop con lai."
        ),
        keywords=["ca hai"],
        any_keywords=["sai", "nhan", "xac dinh", "suy ra"],
        any_min=2,
        max_tokens=400,
    ),

    Question(
        id="L-M3", category="Logic", lang="en", difficulty="Medium",
        prompt=(
            "You are in a room with two doors. One door leads to freedom, "
            "one to a tiger. There are two guards: one always lies, one always tells the truth. "
            "You don't know which is which. You may ask ONE guard ONE yes/no question. "
            "What question do you ask to guarantee finding the freedom door?"
        ),
        reference=(
            "Ask either guard: 'If I asked the OTHER guard which door leads to freedom, "
            "what would he say?' Then take the OPPOSITE door."
        ),
        any_keywords=["other", "opposite", "would say", "liar", "truth"],
        any_min=2,
        open_ended=False,
        max_tokens=350,
    ),

    Question(
        id="L-H1", category="Logic", lang="en", difficulty="Hard",
        prompt=(
            "Five houses in a row. Each house has a different color, "
            "owner of different nationality, different pet, drink, and sport.\n"
            "Clues:\n"
            "1. The Brit lives in the red house.\n"
            "2. The Swede keeps dogs.\n"
            "3. The Dane drinks tea.\n"
            "4. The green house is immediately to the left of the white house.\n"
            "5. The green house owner drinks coffee.\n"
            "6. The person who plays polo keeps birds.\n"
            "7. The owner of the yellow house plays hockey.\n"
            "8. The man in the center house drinks milk.\n"
            "9. The Norwegian lives in the first house.\n"
            "10. The man who plays baseball lives next to the cat owner.\n"
            "11. The horse owner lives next to the hockey player.\n"
            "12. The person who plays billiards drinks beer.\n"
            "13. The German plays soccer.\n"
            "14. The Norwegian lives next to the blue house.\n"
            "15. The baseball player lives next to the water drinker.\n"
            "WHO OWNS THE FISH?"
        ),
        reference="The German owns the fish.",
        any_keywords=["german", "fish"],
        any_min=2,
        max_tokens=600,
    ),

    Question(
        id="L-H2", category="Logic", lang="vi", difficulty="Hard",
        prompt=(
            "Co 4 nguoi: An, Binh, Chi, Dung. "
            "Moi nguoi mac mot mau ao khac nhau: do, xanh, vang, trang.\n"
            "- An khong mac do va khong mac xanh.\n"
            "- Binh mac vang.\n"
            "- Chi khong mac trang.\n"
            "Ai mac ao mau gi? Liet ke day du ca 4 nguoi."
        ),
        reference="An=trang, Binh=vang, Chi=xanh, Dung=do.",
        any_keywords=["an", "binh", "chi", "dung", "vang", "xanh", "trang", "do"],
        any_min=6,
        exact_numbers=[],
        max_tokens=350,
    ),

    # ════════════════════════════════════════════════════════
    # CATEGORY 2: MATHEMATICS (GSM8K / MATH style)
    # ════════════════════════════════════════════════════════

    Question(
        id="M-E1", category="Math", lang="en", difficulty="Easy",
        prompt=(
            "A store sells apples for $0.50 each. "
            "Maria buys 12 apples and pays with a $10 bill. "
            "How much change does she get?"
        ),
        reference="$4.00 change. 12 × $0.50 = $6.00; $10 - $6 = $4.",
        exact_numbers=["4", "4.00"],
        max_tokens=200,
    ),

    Question(
        id="M-E2", category="Math", lang="vi", difficulty="Easy",
        prompt=(
            "Mot to hop sach chia deu cho 6 ke. Moi ke nhan duoc 8 quyen. "
            "Neu chia cho 12 ke, moi ke nhan duoc bao nhieu quyen?"
        ),
        reference="Tong = 6*8 = 48 quyen. Chia cho 12 ke: 48/12 = 4 quyen/ke.",
        exact_numbers=["4", "48"],
        max_tokens=200,
    ),

    Question(
        id="M-M1", category="Math", lang="en", difficulty="Medium",
        prompt=(
            "A train travels at 60 mph for 2 hours, then at 80 mph for 3 hours. "
            "What is the average speed for the entire trip? "
            "Important: do NOT just average 60 and 80. Show full working."
        ),
        reference="Total distance = 120+240 = 360 miles. Total time = 5 hours. Avg speed = 72 mph.",
        exact_numbers=["72"],
        any_keywords=["360", "5 hour", "total distance", "total time"],
        any_min=2,
        max_tokens=300,
    ),

    Question(
        id="M-M2", category="Math", lang="vi", difficulty="Medium",
        prompt=(
            "Voi A mot minh day day be trong 6 gio. "
            "Voi B mot minh day day be trong 3 gio. "
            "Mo ca hai voi cung luc thi bao lau day day be? "
            "Trinh bay cach tinh chi tiet."
        ),
        reference="Toc do: A=1/6 be/gio, B=1/3 be/gio. Tong=1/6+2/6=3/6=1/2 be/gio. Thoi gian=2 gio.",
        exact_numbers=["2"],
        any_keywords=["1/6", "1/3", "1/2"],
        any_min=2,
        max_tokens=350,
    ),

    Question(
        id="M-M3", category="Math", lang="en", difficulty="Medium",
        prompt=(
            "Solve for x: 2x^2 - 5x - 3 = 0. "
            "Use any method (factoring, quadratic formula, or completing the square). "
            "Show all steps."
        ),
        reference="x = 3 or x = -0.5 (discriminant=49, roots via quadratic formula).",
        exact_numbers=["3", "-1/2"],
        max_tokens=400,
    ),

    Question(
        id="M-H1", category="Math", lang="en", difficulty="Hard",
        prompt=(
            "A merchant sells an item at 20% profit. "
            "If he had bought it for 25% less and sold it for $10.50 less, "
            "he would have made 30% profit. "
            "Find the original cost price of the item."
        ),
        reference=(
            "Let CP=x. SP=1.2x. New CP=0.75x. New SP=1.2x-10.50=1.3*0.75x=0.975x. "
            "=> 1.2x-10.50=0.975x => 0.225x=10.50 => x=$46.67."
        ),
        exact_numbers=["46.67", "46.6", "140/3"],
        any_keywords=["0.225", "0.975", "46"],
        any_min=1,
        max_tokens=500,
    ),

    Question(
        id="M-H2", category="Math", lang="vi", difficulty="Hard",
        prompt=(
            "Mot hinh thang co day lon hon day nho 8 cm. "
            "Chieu cao bang trung binh cong cua hai day. "
            "Dien tich hinh thang la 90 cm2. "
            "Tinh do dai cac canh day."
        ),
        reference=(
            "Goi day nho=a, day lon=a+8, chieu cao=(2a+8)/2=a+4. "
            "DT=(a+a+8)/2*(a+4)=(2a+8)/2*(a+4)=(a+4)^2=90. "
            "a+4=sqrt(90)~9.49. a~5.49, a+8~13.49. "
            "Hoac: (a+4)^2=90 => a=sqrt(90)-4."
        ),
        any_keywords=["90", "sqrt", "a+4", "9.49", "5.49"],
        any_min=2,
        max_tokens=500,
    ),

    # ════════════════════════════════════════════════════════
    # CATEGORY 3: CODING  (HumanEval / MBPP style)
    # ════════════════════════════════════════════════════════

    Question(
        id="C-E1", category="Coding", lang="en", difficulty="Easy",
        prompt=(
            "Write a Python function `sum_evens(lst)` that returns the sum of all "
            "even numbers in a list. Example: sum_evens([1,2,3,4,5,6]) should return 12."
        ),
        reference="def sum_evens(lst): return sum(x for x in lst if x % 2 == 0)",
        keywords=["def sum_evens"],
        any_keywords=["% 2", "% 2 == 0", "even", "sum"],
        any_min=2,
        code_to_exec=(
            "RESPONSE_CODE\n"
            "print(sum_evens([1,2,3,4,5,6]))\n"
            "print(sum_evens([]))\n"
            "print(sum_evens([1,3,5]))\n"
        ),
        expected_output="12\n0\n0",
        max_tokens=300,
    ),

    Question(
        id="C-E2", category="Coding", lang="en", difficulty="Easy",
        prompt=(
            "What is the output of this Python code?\n\n"
            "x = [1, 2, 3]\n"
            "y = x\n"
            "y.append(4)\n"
            "print(x)\n\n"
            "Explain WHY in one sentence."
        ),
        reference="[1, 2, 3, 4] because y = x makes both point to the same list object in memory.",
        any_keywords=["[1, 2, 3, 4]", "reference", "same", "object", "memory"],
        any_min=2,
        max_tokens=200,
    ),

    Question(
        id="C-M1", category="Coding", lang="en", difficulty="Medium",
        prompt=(
            "Write a Python function `is_prime(n)` that returns True if n is prime, "
            "False otherwise. Handle edge cases: n<2, n=2, even numbers. "
            "Optimize to check divisors only up to sqrt(n)."
        ),
        reference="Efficient primality test with sqrt optimization and edge case handling.",
        keywords=["def is_prime"],
        any_keywords=["return False", "return True", "** 0.5", "sqrt", "% 2"],
        any_min=3,
        code_to_exec=(
            "RESPONSE_CODE\n"
            "results = [is_prime(n) for n in [-1, 0, 1, 2, 3, 4, 17, 100]]\n"
            "print(results)\n"
        ),
        expected_output="[False, False, False, True, True, False, True, False]",
        max_tokens=400,
    ),

    Question(
        id="C-M2", category="Coding", lang="vi", difficulty="Medium",
        prompt=(
            "Viet ham Python `dem_tu(chuoi)` dem so tu trong mot chuoi. "
            "Tu duoc ngan cach bang khoang trang (co the co nhieu khoang trang lien tiep). "
            "Chuoi rong tra ve 0. "
            "Vi du: dem_tu('  xin   chao  ') = 2."
        ),
        reference="def dem_tu(chuoi): return len(chuoi.split()) if chuoi.strip() else 0",
        keywords=["def dem_tu"],
        any_keywords=["split", "len", "strip"],
        any_min=2,
        code_to_exec=(
            "RESPONSE_CODE\n"
            "print(dem_tu('  xin   chao  '))\n"
            "print(dem_tu(''))\n"
            "print(dem_tu('hello world python'))\n"
        ),
        expected_output="2\n0\n3",
        max_tokens=300,
    ),

    Question(
        id="C-M3", category="Coding", lang="en", difficulty="Medium",
        prompt=(
            "Debug this Python function — it has a bug. Find and fix it:\n\n"
            "def factorial(n):\n"
            "    if n == 0:\n"
            "        return 0\n"
            "    return n * factorial(n - 1)\n\n"
            "Show the corrected function and explain what was wrong."
        ),
        reference="Bug: base case returns 0 instead of 1. Fix: return 1 when n==0.",
        any_keywords=["return 1", "base case", "0", "wrong", "bug", "fix"],
        any_min=3,
        code_to_exec=(
            "RESPONSE_CODE\n"
            "print(factorial(0))\n"
            "print(factorial(5))\n"
            "print(factorial(1))\n"
        ),
        expected_output="1\n120\n1",
        max_tokens=350,
    ),

    Question(
        id="C-H1", category="Coding", lang="en", difficulty="Hard",
        prompt=(
            "Implement a Python function `lcs(s1, s2)` that returns the length of "
            "the Longest Common Subsequence of two strings using dynamic programming.\n"
            "Example: lcs('ABCBDAB', 'BDCAB') should return 4."
        ),
        reference="DP table approach, O(m*n) time. lcs('ABCBDAB','BDCAB')=4.",
        keywords=["def lcs"],
        any_keywords=["dp", "table", "range", "max", "for"],
        any_min=3,
        code_to_exec=(
            "RESPONSE_CODE\n"
            "print(lcs('ABCBDAB', 'BDCAB'))\n"
            "print(lcs('', 'ABC'))\n"
            "print(lcs('ABC', 'ABC'))\n"
        ),
        expected_output="4\n0\n3",
        max_tokens=600,
    ),

    Question(
        id="C-H2", category="Coding", lang="vi", difficulty="Hard",
        prompt=(
            "Viet ham Python `tim_tat_ca_hoan_vi(lst)` tra ve danh sach tat ca hoan vi "
            "cua mot danh sach khong dung ham co san (khong dung itertools). "
            "Vi du: tim_tat_ca_hoan_vi([1,2,3]) tra ve tat ca 6 hoan vi.\n"
            "Chi can tra ve so luong hoan vi la dung."
        ),
        reference="Backtracking recursion. 3! = 6 permutations.",
        keywords=["def tim_tat_ca_hoan_vi"],
        any_keywords=["for", "recursive", "append", "swap", "backtrack"],
        any_min=2,
        code_to_exec=(
            "RESPONSE_CODE\n"
            "result = tim_tat_ca_hoan_vi([1,2,3])\n"
            "print(len(result))\n"
            "result2 = tim_tat_ca_hoan_vi([1])\n"
            "print(len(result2))\n"
        ),
        expected_output="6\n1",
        max_tokens=600,
    ),

    # ════════════════════════════════════════════════════════
    # CATEGORY 4: GENERAL KNOWLEDGE  (MMLU style)
    # ════════════════════════════════════════════════════════

    Question(
        id="G-E1", category="Knowledge", lang="en", difficulty="Easy",
        prompt=(
            "What causes seasons on Earth? "
            "Answer in 2 sentences. Hint: it is NOT because Earth is closer to the Sun."
        ),
        reference="Earth's axial tilt (~23.5 degrees) causes seasons, not distance from the Sun.",
        keywords=["tilt"],
        any_keywords=["axis", "axial", "23.5", "hemisphere", "angle"],
        any_min=2,
        max_tokens=200,
    ),

    Question(
        id="G-E2", category="Knowledge", lang="vi", difficulty="Easy",
        prompt=(
            "Nuoc soi o nhiet do bao nhieu do C o ap suat khi quyen binh thuong? "
            "Va tai sao tren nui cao nuoc soi o nhiet do thap hon?"
        ),
        reference="100 do C. Tren nui cao ap suat khi quyen thap hon, nen nuoc soi o nhiet do thap hon.",
        exact_numbers=["100"],
        any_keywords=["ap suat", "nui", "thap hon", "100"],
        any_min=2,
        max_tokens=200,
    ),

    Question(
        id="G-M1", category="Knowledge", lang="en", difficulty="Medium",
        prompt=(
            "Name THREE structural or chemical differences between DNA and RNA. "
            "Be specific and accurate."
        ),
        reference=(
            "1) Sugar: DNA has deoxyribose, RNA has ribose. "
            "2) Base: DNA uses thymine (T), RNA uses uracil (U). "
            "3) Strands: DNA is double-stranded, RNA is typically single-stranded."
        ),
        any_keywords=["deoxyribose", "ribose", "thymine", "uracil", "double", "single"],
        any_min=4,
        max_tokens=300,
    ),

    Question(
        id="G-M2", category="Knowledge", lang="vi", difficulty="Medium",
        prompt=(
            "Giai thich nguyen ly quang hop (photosynthesis). "
            "Viet phuong trinh hoa hoc tong quat va giai thich y nghia tung thanh phan. "
            "Phan ung xay ra o dau trong te bao?"
        ),
        reference=(
            "6CO2 + 6H2O + anh sang -> C6H12O6 + 6O2. "
            "Xay ra trong luc lap (chloroplast). "
            "CO2 tu khi quyen, H2O tu re cay, nang luong tu anh sang, "
            "san pham la glucose va O2."
        ),
        any_keywords=["co2", "h2o", "glucose", "o2", "luc lap", "chloroplast", "anh sang"],
        any_min=4,
        max_tokens=350,
    ),

    Question(
        id="G-H1", category="Knowledge", lang="en", difficulty="Hard",
        prompt=(
            "Explain the key differences between Type I and Type II errors in statistics. "
            "Give a real-world medical example illustrating each type, "
            "and explain which is typically more dangerous in medical testing and why."
        ),
        reference=(
            "Type I (false positive): reject H0 when true. "
            "Type II (false negative): fail to reject H0 when false. "
            "Medical: Type II (missing disease) usually more dangerous."
        ),
        any_keywords=["false positive", "false negative", "type i", "type ii", "alpha", "beta", "miss"],
        any_min=3,
        max_tokens=450,
    ),

    Question(
        id="G-H2", category="Knowledge", lang="vi", difficulty="Hard",
        prompt=(
            "So sanh co che hoat dong cua vaccine mRNA (nhu Pfizer COVID-19) "
            "voi vaccine truyen thong (nhu vaccine cum). "
            "Neu ro: each loai kich hoat mien dich nhu the nao, "
            "uu nhuoc diem chinh cua moi loai."
        ),
        reference=(
            "mRNA: dua vao te bao dich ma protein gai, kich mien dich, mRNA khong vao nhan. "
            "Truyen thong: virus bat hoat/song yeu/protein. "
            "mRNA: nhanh san xuat, de bien the; truyen thong: chung minh an toan lau dai."
        ),
        any_keywords=["mrna", "protein", "mien dich", "virus", "bat hoat", "kich hoat"],
        any_min=3,
        max_tokens=500,
    ),

    # ════════════════════════════════════════════════════════
    # CATEGORY 5: CRITICAL THINKING & FALLACIES
    # ════════════════════════════════════════════════════════

    Question(
        id="T-E1", category="Critical", lang="en", difficulty="Easy",
        prompt=(
            "Identify the logical fallacy in this argument:\n"
            "'My grandfather smoked all his life and lived to 95. "
            "Therefore, smoking is not harmful.'"
        ),
        reference="Anecdotal evidence / hasty generalization. One case cannot generalize to all.",
        any_keywords=["anecdot", "hasty", "generali", "sample", "one case", "fallacy"],
        any_min=2,
        max_tokens=200,
    ),

    Question(
        id="T-E2", category="Critical", lang="vi", difficulty="Easy",
        prompt=(
            "Phan tich loi tu duy trong cau sau:\n"
            "'Toi uong nuoc chanh moi sang va chua bao gio bi ung thu. "
            "Vay nuoc chanh ngan ngua ung thu.'"
        ),
        reference="Loi tuong quan nhan qua (correlation != causation). Mot mau don le khong du chung minh.",
        any_keywords=["tuong quan", "nhan qua", "correlation", "causation", "mau", "chung minh"],
        any_min=3,
        max_tokens=250,
    ),

    Question(
        id="T-M1", category="Critical", lang="en", difficulty="Medium",
        prompt=(
            "A study claims: 'Students who eat breakfast score higher on exams.' "
            "List THREE alternative explanations (confounders) that could explain "
            "this correlation WITHOUT breakfast causing better scores."
        ),
        reference=(
            "Confounders: socioeconomic status, sleep quality, parental involvement, "
            "general health habits, school type."
        ),
        any_keywords=["confounder", "correlation", "socioeconomic", "habit", "alternative", "cause"],
        any_min=3,
        max_tokens=300,
    ),

    Question(
        id="T-M2", category="Critical", lang="vi", difficulty="Medium",
        prompt=(
            "Spot the logical fallacy and name it:\n"
            "'Tat ca lanh dao vi dai deu la nguoi dam mao hiem. "
            "Elon Musk la nguoi dam mao hiem. "
            "Vay Elon Musk la lanh dao vi dai.'"
        ),
        reference="Affirming the consequent (khang dinh hau qua). Dam mao hiem la dieu kien can nhung khong du.",
        any_keywords=["consequent", "hau qua", "can", "du", "fallacy", "khong du"],
        any_min=2,
        max_tokens=300,
    ),

    Question(
        id="T-H1", category="Critical", lang="en", difficulty="Hard",
        prompt=(
            "A pharmaceutical company releases a study showing their new drug reduces "
            "heart attacks by 50% (relative risk reduction). "
            "However, the absolute risk went from 2% to 1%. "
            "Explain: (a) the difference between relative and absolute risk reduction, "
            "(b) why the 50% claim is misleading, "
            "(c) what number-needed-to-treat (NNT) means here."
        ),
        reference=(
            "RRR=50% (1%/2%), ARR=1% (2%-1%). "
            "NNT=1/ARR=100 (treat 100 patients to prevent 1 heart attack). "
            "50% sounds dramatic but absolute benefit is small."
        ),
        any_keywords=["absolute", "relative", "nnt", "number needed", "1%", "mislead", "100"],
        any_min=4,
        max_tokens=500,
    ),

    Question(
        id="T-H2", category="Critical", lang="vi", difficulty="Hard",
        prompt=(
            "Phan tich tranh luan sau va chi ra tat ca cac loi lap luan:\n\n"
            "'Chinh sach mo cua hang ban le 24/7 se gay hai cho xa hoi. "
            "Nhung nguoi phan doi la nhung ke luoi bieng khong muon lam viec. "
            "Tat ca cac nuoc van minh deu co cua hang mo 24/7. "
            "Neu ban khong dong y, ban dang ung ho nen kinh te lac hau.'"
        ),
        reference=(
            "Cac loi: Ad hominem (tan cong nguoi phan doi), "
            "Appeal to majority/civilization (fallacy of appeal to authority/bandwagon), "
            "False dilemma (chi co 2 lua chon), "
            "Non sequitur (ket luan khong theo sau tien de)."
        ),
        any_keywords=["ad hominem", "straw man", "false dilemma", "bandwagon", "appeal", "loi"],
        any_min=3,
        open_ended=True,
        max_tokens=500,
    ),

    # ════════════════════════════════════════════════════════
    # CATEGORY 6: LANGUAGE & COMPREHENSION
    # ════════════════════════════════════════════════════════

    Question(
        id="LA-E1", category="Language", lang="en", difficulty="Easy",
        prompt=(
            "Rewrite this sentence to fix the grammatical error:\n"
            "'The team have decided to cancelled their plans due to the weathers.'"
        ),
        reference="'The team has decided to cancel their plans due to the weather.'",
        any_keywords=["has decided", "cancel", "weather"],
        any_min=2,
        max_tokens=150,
    ),

    Question(
        id="LA-E2", category="Language", lang="vi", difficulty="Easy",
        prompt=(
            "Viet lai cau sau theo gong van trang trong hon, "
            "giu nguyen y nghia:\n"
            "'May tinh cua tao bi hu roi, buon qua.'"
        ),
        reference="'May tinh cua toi da bi hong, toi cam thay rat buon long.'",
        any_keywords=["may tinh", "hong", "buon"],
        any_min=2,
        max_tokens=150,
    ),

    Question(
        id="LA-M1", category="Language", lang="en", difficulty="Medium",
        prompt=(
            "Read this paragraph and answer: What is the author's main argument, "
            "and what evidence do they provide?\n\n"
            "'Remote work has transformed modern employment. Studies show that remote "
            "workers report 22% higher productivity and 40% less stress. Companies "
            "like GitLab and Automattic have operated fully remotely for years with "
            "record profits. Critics argue that collaboration suffers, but data from "
            "Stanford shows creative problem-solving actually improves with async communication.'"
        ),
        reference=(
            "Main argument: remote work is beneficial. "
            "Evidence: 22% productivity increase, 40% less stress, GitLab/Automattic success, Stanford data."
        ),
        any_keywords=["remote", "productivity", "22%", "stanford", "argument", "evidence"],
        any_min=3,
        max_tokens=300,
    ),

    Question(
        id="LA-M2", category="Language", lang="vi", difficulty="Medium",
        prompt=(
            "Tom tat doan van sau trong khong qua 3 cau, "
            "giu lai cac y chinh:\n\n"
            "'Bien doi khi hau dang anh huong nghiem trong den nong nghiep Viet Nam. "
            "Han han keo dai o mien Trung, lu lut o dong bang song Cuu Long, "
            "va nhiet do tang lam giam nang suat lua. "
            "Chinh phu dang thuc hien cac bien phap thich ung nhu trong cac giong lua "
            "chiu nhiet va xay dung he thong tuoi tieu hien dai. "
            "Tuy nhien, cac chuyen gia canh bao rang neu khong co hanh dong quoc te, "
            "Viet Nam co the mat di 12% dien tich dat canh tac vao nam 2050.'"
        ),
        reference=(
            "Bien doi khi hau gay tac dong nghiem trong den nong nghiep Viet Nam (han han, lu lut, nang suat giam). "
            "Chinh phu dang co bien phap thich ung. "
            "Khong hanh dong quoc te, Viet Nam co the mat 12% dat canh tac vao 2050."
        ),
        any_keywords=["bien doi", "nong nghiep", "han han", "12%", "2050", "thich ung"],
        any_min=3,
        max_tokens=250,
    ),

    Question(
        id="LA-H1", category="Language", lang="en", difficulty="Hard",
        prompt=(
            "Translate this Vietnamese proverb to English and explain its cultural meaning:\n"
            "'Mot cay lam chang nen non, ba cay chum lai nen hon nui cao.'"
        ),
        reference=(
            "Literal: 'One tree cannot make a mountain; three trees together make a high mountain.' "
            "Meaning: Unity and collective effort achieve what individuals cannot alone. "
            "Cultural: emphasizes community over individualism in Vietnamese culture."
        ),
        any_keywords=["unity", "together", "collective", "mountain", "tree", "alone", "community"],
        any_min=3,
        max_tokens=300,
    ),

    # ════════════════════════════════════════════════════════
    # CATEGORY 7: COMMON SENSE & WORLD KNOWLEDGE (HellaSwag)
    # ════════════════════════════════════════════════════════

    Question(
        id="CS-E1", category="Common Sense", lang="en", difficulty="Easy",
        prompt=(
            "Which continuation makes most sense?\n"
            "A person is cooking pasta. They boil water, add salt, and put in the pasta.\n"
            "A) They immediately serve the raw pasta to guests.\n"
            "B) They wait 8-10 minutes, then drain and serve.\n"
            "C) They add ice cubes to stop the water from boiling.\n"
            "D) They put the pot in the refrigerator.\n"
            "Answer with the letter and briefly explain."
        ),
        reference="B - wait 8-10 minutes then drain and serve (standard pasta cooking).",
        keywords=["b"],
        max_tokens=150,
    ),

    Question(
        id="CS-E2", category="Common Sense", lang="vi", difficulty="Easy",
        prompt=(
            "Tiep theo hop ly nhat la gi?\n"
            "Mot nguoi dang o trong nha va nghe thay tieng sam set lon o ben ngoai.\n"
            "A) Ho chay ra ngoai de nhin troi.\n"
            "B) Ho tat tat ca thiet bi dien va tram that an toan trong nha.\n"
            "C) Ho bat tat ca den de nhin duoc ro hon.\n"
            "D) Ho mo cua so de nghe sam trot ro hon.\n"
            "Chon dap an va giai thich."
        ),
        reference="B - tat thiet bi dien va tram an toan la hanh dong an toan nhat khi co bao.",
        keywords=["b"],
        max_tokens=150,
    ),

    Question(
        id="CS-M1", category="Common Sense", lang="en", difficulty="Medium",
        prompt=(
            "A doctor prescribes medication and tells a patient to take it "
            "'three times a day with food.' The patient has breakfast at 7am, "
            "lunch at 12pm, and dinner at 6pm. "
            "The patient wakes up at 3am feeling unwell and realizes they forgot the evening dose. "
            "What should the patient most likely do, and why?"
        ),
        reference=(
            "Skip the missed dose and take the next one as scheduled at breakfast. "
            "Do not double dose. General medical advice is never to catch up with double doses."
        ),
        any_keywords=["skip", "next dose", "do not double", "morning", "breakfast"],
        any_min=2,
        max_tokens=250,
    ),

    Question(
        id="CS-M2", category="Common Sense", lang="vi", difficulty="Medium",
        prompt=(
            "Ban dang o mot thanh pho la la. Ban het tien va pin dien thoai sap het. "
            "Ban can tim nha hang can nhat. Sap xep thu tu uu tien cac hanh dong sau:\n"
            "A) Tim wifi cong cong de dung ban do\n"
            "B) Hoi nguoi di duong\n"
            "C) Tim noi sac dien thoai truoc\n"
            "D) Di bo theo ngu giac tim nha hang\n"
            "Giai thich lua chon cua ban."
        ),
        reference=(
            "Uu tien: B (hoi nguoi di duong - nhanh nhat, khong can pin), "
            "sau do A (neu con pin), sau C neu can ban do lau dai, D la phoi lieu."
        ),
        any_keywords=["hoi", "nguoi", "nhanh", "pin", "wifi"],
        any_min=2,
        open_ended=True,
        max_tokens=300,
    ),

    # ════════════════════════════════════════════════════════
    # CATEGORY 8: CALIBRATION & SELF-AWARENESS
    # ════════════════════════════════════════════════════════

    Question(
        id="CA-E1", category="Calibration", lang="en", difficulty="Easy",
        prompt=(
            "What is 2 + 2? Answer with just the number, then rate your confidence "
            "as a percentage (0-100%)."
        ),
        reference="4. Confidence should be 100%.",
        exact_numbers=["4"],
        any_keywords=["100", "certain", "sure", "confident"],
        any_min=1,
        max_tokens=100,
    ),

    Question(
        id="CA-M1", category="Calibration", lang="en", difficulty="Medium",
        prompt=(
            "I will ask you about the exact population of Ho Chi Minh City as of today. "
            "Before answering: state clearly if you are CERTAIN or UNCERTAIN, "
            "give your best estimate with a range, "
            "and explain why you may not be perfectly accurate."
        ),
        reference=(
            "~9-13 million (metro area). Should express uncertainty about exact current figures, "
            "mention knowledge cutoff, and give a reasonable range."
        ),
        any_keywords=["million", "uncertain", "estimate", "range", "cutoff", "approximate"],
        any_min=3,
        max_tokens=300,
    ),

    Question(
        id="CA-H1", category="Calibration", lang="en", difficulty="Hard",
        prompt=(
            "Answer this question, but BEFORE answering, assess your confidence (0-100%) "
            "and explain your uncertainty sources:\n\n"
            "What was the exact GDP of Vietnam in Q3 2024, in USD?"
        ),
        reference=(
            "Should express uncertainty (exact quarterly GDP is hard to recall precisely), "
            "give approximate range (~100-120B USD for Q3 estimate), cite knowledge cutoff limitation."
        ),
        any_keywords=["uncertain", "estimate", "billion", "gdp", "range", "cutoff", "exact"],
        any_min=4,
        open_ended=True,
        max_tokens=350,
    ),

    # ════════════════════════════════════════════════════════
    # CATEGORY 9: TOOL USE (FUNCTION CALLING)
    # Structural eval (BFCL-style): check tool name + args, no execution
    # ════════════════════════════════════════════════════════

    # ── Easy ────────────────────────────────────────────────

    Question(
        id="TU-E1", category="ToolUse", lang="en", difficulty="Easy",
        prompt=(
            "What is the current weather in Hanoi? "
            "Use the available tool to get this information. "
            "I prefer temperatures in Celsius."
        ),
        reference="Call get_weather with city='Hanoi' and unit='celsius'.",
        tools=[{
            "type": "function",
            "function": {
                "name": "get_weather",
                "description": "Get current weather for a city.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "city": {"type": "string", "description": "City name"},
                        "unit": {"type": "string", "enum": ["celsius", "fahrenheit"],
                                 "description": "Temperature unit"},
                    },
                    "required": ["city"],
                },
            },
        }],
        expected_tool_calls=[{"name": "get_weather", "args": {"city": "Hanoi", "unit": "celsius"}}],
        max_tokens=256,
    ),

    Question(
        id="TU-E2", category="ToolUse", lang="en", difficulty="Easy",
        prompt=(
            "I have 500 US dollars. Use the currency converter tool "
            "to convert them to Euros (EUR)."
        ),
        reference="Call convert_currency with amount=500, from_currency='USD', to_currency='EUR'.",
        tools=[{
            "type": "function",
            "function": {
                "name": "convert_currency",
                "description": "Convert an amount from one currency to another.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "amount": {"type": "number", "description": "Amount to convert"},
                        "from_currency": {"type": "string", "description": "Source currency code (e.g. USD)"},
                        "to_currency": {"type": "string", "description": "Target currency code (e.g. EUR)"},
                    },
                    "required": ["amount", "from_currency", "to_currency"],
                },
            },
        }],
        expected_tool_calls=[{"name": "convert_currency",
                               "args": {"amount": 500, "from_currency": "USD", "to_currency": "EUR"}}],
        max_tokens=256,
    ),

    Question(
        id="TU-E3", category="ToolUse", lang="en", difficulty="Easy",
        prompt=(
            "Please set a reminder for me: 'Take medication' in 30 minutes."
        ),
        reference="Call set_reminder with message='Take medication' and time_minutes=30.",
        tools=[{
            "type": "function",
            "function": {
                "name": "set_reminder",
                "description": "Set a reminder with a message after a given number of minutes.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "message": {"type": "string", "description": "Reminder message"},
                        "time_minutes": {"type": "integer", "description": "Minutes from now"},
                    },
                    "required": ["message", "time_minutes"],
                },
            },
        }],
        expected_tool_calls=[{"name": "set_reminder",
                               "args": {"message": "Take medication", "time_minutes": 30}}],
        max_tokens=256,
    ),

    # ── Medium ───────────────────────────────────────────────

    Question(
        id="TU-M1", category="ToolUse", lang="en", difficulty="Medium",
        prompt=(
            "I want to know the AAPL stock price in USD, then convert that amount to VND. "
            "Use the tools to do both operations."
        ),
        reference=(
            "Should call get_stock_price(symbol='AAPL') AND convert_currency "
            "with from_currency='USD', to_currency='VND'."
        ),
        tools=[
            {
                "type": "function",
                "function": {
                    "name": "get_stock_price",
                    "description": "Get the current price of a stock by ticker symbol.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "symbol": {"type": "string", "description": "Stock ticker symbol (e.g. AAPL)"},
                        },
                        "required": ["symbol"],
                    },
                },
            },
            {
                "type": "function",
                "function": {
                    "name": "convert_currency",
                    "description": "Convert an amount from one currency to another.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "amount": {"type": "number"},
                            "from_currency": {"type": "string"},
                            "to_currency": {"type": "string"},
                        },
                        "required": ["amount", "from_currency", "to_currency"],
                    },
                },
            },
        ],
        expected_tool_calls=[
            {"name": "get_stock_price", "args": {"symbol": "AAPL"}},
            {"name": "convert_currency", "args": {"from_currency": "USD", "to_currency": "VND"}},
        ],
        max_tokens=512,
    ),

    Question(
        id="TU-M2", category="ToolUse", lang="en", difficulty="Medium",
        prompt=(
            "What is the capital city of France? Answer directly — do not use any tool."
        ),
        reference=(
            "Should NOT call web_search. Should answer directly: Paris is the capital of France."
        ),
        tools=[{
            "type": "function",
            "function": {
                "name": "web_search",
                "description": "Search the web for real-time information.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "query": {"type": "string", "description": "Search query"},
                    },
                    "required": ["query"],
                },
            },
        }],
        expected_tool_calls=[],      # No tool call expected
        irrelevant_tools=["web_search"],
        keywords=["paris"],
        max_tokens=256,
    ),

    Question(
        id="TU-M3", category="ToolUse", lang="en", difficulty="Medium",
        prompt=(
            "Schedule a meeting called 'Q3 Planning' for tomorrow from 09:00 to 10:30, "
            "with attendees alice@example.com and bob@example.com."
        ),
        reference=(
            "Call create_calendar_event with title='Q3 Planning', start_time='09:00', "
            "end_time='10:30', attendees=['alice@example.com', 'bob@example.com']."
        ),
        tools=[{
            "type": "function",
            "function": {
                "name": "create_calendar_event",
                "description": "Create a calendar event.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "title": {"type": "string"},
                        "start_time": {"type": "string", "description": "HH:MM format"},
                        "end_time": {"type": "string", "description": "HH:MM format"},
                        "attendees": {"type": "array", "items": {"type": "string"},
                                      "description": "List of attendee emails"},
                    },
                    "required": ["title", "start_time", "end_time"],
                },
            },
        }],
        expected_tool_calls=[{
            "name": "create_calendar_event",
            "args": {
                "title": "Q3 Planning",
                "start_time": "09:00",
                "end_time": "10:30",
            },
        }],
        max_tokens=512,
    ),

    # ── Hard ─────────────────────────────────────────────────

    Question(
        id="TU-H1", category="ToolUse", lang="en", difficulty="Hard",
        prompt=(
            "I need to: (1) get the weather in Tokyo in Fahrenheit, "
            "(2) search for 'best restaurants in Tokyo'. "
            "Do NOT send any emails. Use tools for both weather and search."
        ),
        reference=(
            "Call get_weather(city='Tokyo', unit='fahrenheit') AND "
            "web_search(query='best restaurants in Tokyo'). "
            "Should NOT call send_email."
        ),
        tools=[
            {
                "type": "function",
                "function": {
                    "name": "get_weather",
                    "description": "Get current weather for a city.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "city": {"type": "string"},
                            "unit": {"type": "string", "enum": ["celsius", "fahrenheit"]},
                        },
                        "required": ["city"],
                    },
                },
            },
            {
                "type": "function",
                "function": {
                    "name": "web_search",
                    "description": "Search the web.",
                    "parameters": {
                        "type": "object",
                        "properties": {"query": {"type": "string"}},
                        "required": ["query"],
                    },
                },
            },
            {
                "type": "function",
                "function": {
                    "name": "send_email",
                    "description": "Send an email.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "to": {"type": "string"},
                            "subject": {"type": "string"},
                            "body": {"type": "string"},
                        },
                        "required": ["to", "subject", "body"],
                    },
                },
            },
        ],
        expected_tool_calls=[
            {"name": "get_weather", "args": {"city": "Tokyo", "unit": "fahrenheit"}},
            {"name": "web_search", "args": {"query": "best restaurants in Tokyo"}},
        ],
        irrelevant_tools=["send_email"],
        max_tokens=512,
    ),

    Question(
        id="TU-H2", category="ToolUse", lang="en", difficulty="Hard",
        prompt=(
            "What is 15% of 240? Just calculate it mentally and tell me the answer. "
            "No tools needed."
        ),
        reference=(
            "Should NOT call any tool. Direct answer: 15% of 240 = 36."
        ),
        tools=[
            {
                "type": "function",
                "function": {
                    "name": "calculator",
                    "description": "Perform arithmetic calculations.",
                    "parameters": {
                        "type": "object",
                        "properties": {"expression": {"type": "string"}},
                        "required": ["expression"],
                    },
                },
            },
            {
                "type": "function",
                "function": {
                    "name": "web_search",
                    "description": "Search the web.",
                    "parameters": {
                        "type": "object",
                        "properties": {"query": {"type": "string"}},
                        "required": ["query"],
                    },
                },
            },
        ],
        expected_tool_calls=[],       # No tool call expected
        irrelevant_tools=["calculator", "web_search"],
        keywords=["36"],
        max_tokens=256,
    ),
]

# Deduplicate by id (keep last occurrence)
_seen: dict[str, Question] = {}
for q in QUESTIONS:
    _seen[q.id] = q
QUESTIONS = list(_seen.values())
