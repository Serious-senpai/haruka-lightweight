import "package:flutter/material.dart";

import "assets.dart";

class User {
  final String id;
  final String name;
  final String discriminator;

  final Asset? avatar;

  String get displayName => "$name#$discriminator";

  User(Map<String, dynamic> data)
      : id = data["id"]!,
        name = data["name"]!,
        discriminator = data["discriminator"]!,
        avatar = data["avatar"] != null ? Asset(data["avatar"]!) : null;

  Widget displayAvatar({double? size}) => avatar == null
      ? CircleAvatar(
          backgroundColor: Colors.black,
          child: Text(name),
        )
      : CircleAvatar(backgroundImage: NetworkImage(avatar!.url));

  @override
  bool operator ==(covariant User other) => id == other.id;

  @override
  int get hashCode => id.hashCode;
}
