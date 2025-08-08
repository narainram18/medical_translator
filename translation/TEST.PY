import argostranslate.package
import argostranslate.translate
import time

print("🔄 Fetching package index...")
argostranslate.package.update_package_index()
available_packages = argostranslate.package.get_available_packages()

installed_pairs = set()
success_count = 0
fail_count = 0

print("⬇️ Starting download and installation of language models...\n")

for pkg in available_packages:
    from_code = pkg.from_code
    to_code = pkg.to_code

    # Skip Tamil
    if from_code == "ta" or to_code == "ta":
        continue

    if (from_code, to_code) in installed_pairs:
        continue

    try:
        print(f"📦 Installing model: {pkg.from_name} ({from_code}) → {pkg.to_name} ({to_code})")
        download_path = pkg.download()
        argostranslate.package.install_from_path(download_path)
        installed_pairs.add((from_code, to_code))
        success_count += 1
        # Sleep 1 second to be gentle with servers
        time.sleep(1)
    except Exception as e:
        print(f"❌ Failed to install {from_code} -> {to_code}: {e}")
        fail_count += 1

print(f"\n✅ Installed {success_count} language models successfully.")
if fail_count > 0:
    print(f"⚠️ Failed to install {fail_count} models.")
else:
    print("🎉 All available language models installed successfully (excluding Tamil).")
