# -*- coding: utf-8 -*-
"""按番号批量下载字幕: subtitlecat(一级) + 迅雷字幕API(二级补充)。
用法: python sub_dl.py <目录树txt路径> [输出目录]
	会从 UTF-16/UTF-8 自动解码，提取番号正则 [A-Z]{2,6}[-_]\d{2,6}，先跑 subtitlecat，
	NONE 的转迅雷补，两站都没有的导出 _未找到字幕清单.txt 到输出目录。"""
import os, re, sys, time
import requests
from bs4 import BeautifulSoup

BASE = "https://www.subtitlecat.com"
XL_API = "https://api-shoulei-ssl.xunlei.com/oracle/subtitle?name={}"
UA = {"User-Agent": "Mozilla/5.0"}
S = requests.Session(); S.headers.update(UA)
OUT = sys.argv[2] if len(sys.argv) > 2 else r"C:/Users/jams_/Downloads/字幕"
os.makedirs(OUT, exist_ok=True)


def get(url, **kw):
	for _ in range(3):
		try:
			r = S.get(url, timeout=25, **kw)
			if r.status_code == 200:
				return r
		except Exception:
			pass
		time.sleep(2)
	return None


def read_codes(path):
	raw = open(path, "rb").read()
	for enc in ("utf-16", "utf-8", "gbk"):
		try:
			t = raw.decode(enc)
		except Exception:
			continue
		break
	else:
		t = raw.decode("utf-8", "ignore")
	seen, out = set(), []
	for c in re.findall(r"[A-Z]{2,6}[-_]\d{2,6}", t):
		cu = c.upper().replace("_", "-")
		if cu not in seen:
			seen.add(cu); out.append(cu)
	return out


def zh_score(name):
	n = name.lower()
	return 2 if any(k in n for k in ("zh", "chs", "cht", "简", "中文", "chi")) else 1


def exists(code):
	return any(f.upper().startswith(code) for f in os.listdir(OUT))


def sc_process(code):
	if exists(code):
		return "skip"
	r = get(f"{BASE}/index.php?search={code}")
	if not r:
		return "FAIL(搜索)"
	soup = BeautifulSoup(r.text, "html.parser")
	detail = None
	cu = code.replace("-", "")
	for a in soup.select("td a[href]"):
		if cu in a.get_text().upper().replace("-", "").replace("_", ""):
			detail = a["href"]; break
	if not detail:
		return "NONE"
	r2 = get(BASE + "/" + detail.lstrip("/"))
	if not r2:
		return "FAIL(详情)"
	s2 = BeautifulSoup(r2.text, "html.parser")
	links = [a["href"] for a in s2.select("a[href]") if a.get("href", "").endswith(".srt")]
	if not links:
		return "NONE(无srt)"
	for key in ("zh-CN", "Chinese", "zh-TW", "chi"):
		for h in links:
			if key.lower() in (h + a.get_text()).lower():
				return ("OK(zh)", h, "zh")
	return ("OK", links[0], "other")


def xl_process(code):
	try:
		data = S.get(XL_API.format(code), timeout=20).json().get("data") or []
	except Exception:
		return ("FAIL(api)", None, None)
	cands = [d for d in data if code.replace("-", "") in d.get("name", "").upper().replace("-", "").replace("_", "")] or data
	if not cands:
		return ("NONE", None, None)
	cands.sort(key=lambda d: zh_score(d.get("name", "")), reverse=True)
	for d in cands[:3]:
		try:
			r2 = S.get(d["url"], timeout=25)
			if r2.status_code == 200 and len(r2.content) > 500:
				tag = "zh" if zh_score(d.get("name", "")) == 2 else "xl"
				return ("OK", d["url"], tag, d.get("ext", "srt") or "srt")
		except Exception:
			continue
	return ("FAIL(下载)", None, None)


def main():
	codes = read_codes(sys.argv[1])
	print(f"共 {len(codes)} 个番号", flush=True)
	missing, ok = [], 0
	for i, c in enumerate(codes, 1):
		res, *rest = sc_process(c)
		if res in ("OK", "skip"):
			ok += 1
			if res == "OK":
				url, tag = rest[0], rest[1]
				ext = "srt"
				open(os.path.join(OUT, f"{c}.{tag}.{ext}"), "wb").write(get(url).content)
			print(f"[SC {i}/{len(codes)}] {c}: {res}", flush=True)
		else:
			missing.append(c)
			print(f"[SC {i}/{len(codes)}] {c}: {res}", flush=True)
		time.sleep(1)
	ok2 = none = fail = 0
	still = []
	for i, c in enumerate(missing, 1):
		res, *rest = xl_process(c)
		if res == "OK":
			ok2 += 1
			url, tag, ext = rest
			open(os.path.join(OUT, f"{c}.{tag}.{ext}"), "wb").write(S.get(url).content)
			print(f"[XL {i}] {c}: OK", flush=True)
		elif res == "NONE":
			none += 1; still.append(c); print(f"[XL {i}] {c}: NONE", flush=True)
		else:
			fail += 1; still.append(c); print(f"[XL {i}] {c}: {res}", flush=True)
		time.sleep(0.5)
	with open(os.path.join(OUT, "_未找到字幕清单.txt"), "w", encoding="utf-8") as f:
		f.write(f"两站均未找到，共{len(still)}个\n\n" + "\n".join(still))
	print(f"\n完成: subtitlecat {ok} + 迅雷 {ok2} = {ok+ok2}/{len(codes)}，未找到 {len(still)}", flush=True)


if __name__ == "__main__":
	main()
