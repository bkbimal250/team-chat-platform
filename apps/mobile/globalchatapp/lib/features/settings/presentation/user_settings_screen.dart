import 'dart:async';
import 'package:image_picker/image_picker.dart';
import 'package:mime/mime.dart';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../../../services/api/providers/api_providers.dart';

class UserSettingsScreen extends ConsumerStatefulWidget {
  const UserSettingsScreen({super.key, this.privacy = false});
  final bool privacy;
  @override
  ConsumerState<UserSettingsScreen> createState() => _UserSettingsScreenState();
}
class _UserSettingsScreenState extends ConsumerState<UserSettingsScreen> {
  final _name = TextEditingController();
  final _about = TextEditingController();
  final _form = GlobalKey<FormState>();
  Map<String, dynamic>? _data;
  bool _saving = false;
  String? _photoUrl;
  String _duration = 'always';
  final _hours = TextEditingController(text: '24');
  Timer? _photoRefresh;
  Future<void> _refreshPhoto(String id) async {
    try {
      final url = await ref.read(userApiProvider).photoUrl(id);
      if (mounted) setState(() => _photoUrl = url);
    } catch (_) { if (mounted) setState(() => _photoUrl = null); }
    if (mounted) _photoRefresh = Timer(const Duration(seconds: 30), () => _refreshPhoto(id));
  }
  Future<void> _changePhoto() async {
    final hours = _duration == 'always' ? null : _duration == '24' ? 24 : int.tryParse(_hours.text);
    if (_duration != 'always' && (hours == null || hours < 1 || hours > 8760)) {
      setState(() => _error = 'Choose 1 to 8760 hours.'); return;
    }
    setState(() { _saving = true; _error = null; });
    try {
      final image = await ImagePicker().pickImage(source: ImageSource.gallery, maxWidth: 512, maxHeight: 512, imageQuality: 85);
      if (image == null || !mounted) return;
      final bytes = await image.readAsBytes();
      final mime = lookupMimeType(image.name, headerBytes: bytes);
      if (!['image/jpeg','image/png','image/webp'].contains(mime)) throw ArgumentError('Unsupported image');
      await ref.read(userApiProvider).setPhoto(bytes, mime!, hours);
      if (mounted) await _load();
    } catch (_) { if (mounted) setState(() => _error = 'Could not save photo. Use a JPEG, PNG or WebP under 2 MB.'); }
    finally { if (mounted) setState(() => _saving = false); }
  }
  Future<void> _removePhoto() async {
    setState(() => _saving = true);
    try { await ref.read(userApiProvider).removePhoto(); if (mounted) await _load(); }
    catch (_) { if (mounted) setState(() => _error = 'Could not remove photo.'); }
    finally { if (mounted) setState(() => _saving = false); }
  }
  String? _error;
  String get _section => widget.privacy ? '/privacy' : '';
  @override
  void initState() { super.initState(); Future.microtask(_load); }
  @override
  void dispose() { _name.dispose(); _about.dispose(); super.dispose(); }
  Future<void> _load() async {
    try {
      final data = await ref.read(userApiProvider).get(_section);
      if (!mounted) return;
      _photoRefresh?.cancel();
      _photoUrl = null;
      final photoId = data['avatar_media_id'] as String?;
      if (photoId != null) unawaited(_refreshPhoto(photoId));
      _name.text = data['display_name'] as String? ?? '';
      _about.text = data['about'] as String? ?? '';
      setState(() { _data = data; _error = null; });
    } catch (_) { if (mounted) setState(() => _error = 'Could not load settings. Please retry.'); }
  }
  Future<void> _save() async {
    if (_saving || !(_form.currentState?.validate() ?? false)) return;
    setState(() { _saving = true; _error = null; });
    try {
      final values = widget.privacy ? Map<String, dynamic>.from(_data!) :
        <String, dynamic>{'display_name': _name.text.trim(), 'about': _about.text.trim()};
      final updated = await ref.read(userApiProvider).update(_section, values);
      if (!mounted) return;
      setState(() => _data = updated);
      ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content: Text('Settings saved')));
    } catch (_) { if (mounted) setState(() => _error = 'Could not save settings. Please retry.'); }
    finally { if (mounted) setState(() => _saving = false); }
  }
  @override
  Widget build(BuildContext context) => Scaffold(
    appBar: AppBar(title: Text(widget.privacy ? 'Privacy' : 'Profile')),
    body: _data == null ? Center(child: _error == null ? const CircularProgressIndicator() :
      Column(mainAxisSize: MainAxisSize.min, children: [Text(_error!), TextButton(onPressed: _load, child: const Text('Retry'))])) :
    Form(key: _form, child: ListView(padding: const EdgeInsets.all(20), children: [
      if (!widget.privacy) ...[
                    Center(child: CircleAvatar(radius: 44, backgroundImage: _photoUrl == null ? null : NetworkImage(_photoUrl!), child: _photoUrl == null ? const Icon(Icons.person, size: 40) : null)),
                    DropdownButtonFormField<String>(initialValue: _duration,
                      decoration: const InputDecoration(labelText: 'Keep profile photo for'),
                      items: const [DropdownMenuItem(value:'always',child:Text('Always')), DropdownMenuItem(value:'24',child:Text('24 hours')), DropdownMenuItem(value:'custom',child:Text('Custom hours'))],
                      onChanged: _saving ? null : (v) => setState(() => _duration = v!)),
                    if (_duration == 'custom') TextField(controller: _hours, keyboardType: TextInputType.number,
                      decoration: const InputDecoration(labelText: 'Hours (1–8760)')),
                    Text(_data!['avatar_expires_at'] == null ? 'No expiry set' : 'Expires: ${_data!['avatar_expires_at']}'),
                    const Text('Expired photos return to initials. Your photo privacy settings still apply.'),
                    TextButton(onPressed: _saving ? null : _changePhoto, child: const Text('Change photo')),
                    if (_data!['avatar_media_id'] != null) TextButton(onPressed: _saving ? null : _removePhoto, child: const Text('Remove photo')),

        TextFormField(controller: _name, maxLength: 200, enabled: !_saving,
          decoration: const InputDecoration(labelText: 'Display name'),
          validator: (value) => value == null || value.trim().isEmpty ? 'Enter your name' : null),
        TextFormField(controller: _about, maxLength: 2000, maxLines: 4, enabled: !_saving,
          decoration: const InputDecoration(labelText: 'About')),
      ] else ...[
        for (final field in const {'profile_photo_visibility':'Profile photo', 'about_visibility':'About',
          'online_status_visibility':'Online status', 'last_seen_visibility':'Last seen'}.entries)
          Padding(padding: const EdgeInsets.symmetric(vertical: 12), child: DropdownButtonFormField<String>(
            initialValue: _data![field.key] as String?, decoration: InputDecoration(labelText: field.value),
            items: const [DropdownMenuItem(value:'EVERYONE',child:Text('Everyone')),
              DropdownMenuItem(value:'ORGANIZATION',child:Text('Organization members')),
              DropdownMenuItem(value:'CONTACTS',child:Text('My contacts')),
              DropdownMenuItem(value:'NOBODY',child:Text('Nobody'))],
            onChanged: _saving ? null : (value) => setState(() => _data![field.key] = value))),
        for (final field in const {'read_receipts_enabled':'Read receipts', 'discoverable':'Allow contact discovery'}.entries)
          SwitchListTile(title: Text(field.value), value: _data![field.key] == true,
            onChanged: _saving ? null : (value) => setState(() => _data![field.key] = value)),
      ],
      if (_error != null) Text(_error!),
      const SizedBox(height: 20),
      FilledButton(onPressed: _saving ? null : _save, child: Text(_saving ? 'Saving...' : 'Save changes')),
    ])),
  );
}
