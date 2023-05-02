class Asset {
  final String key;
  final String url;

  Asset(Map<String, String> data)
      : key = data["key"]!,
        url = data["url"]!;
}
