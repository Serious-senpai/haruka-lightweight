import "package:flutter/material.dart";

import "assets.dart";

class User {
  final String id;
  final String name;

  final Asset? avatar;

  String get displayName => name;

  User(Map<String, dynamic> data)
      : id = data["id"]!,
        name = data["name"]!,
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

  @override
  String toString() => displayName;
}
