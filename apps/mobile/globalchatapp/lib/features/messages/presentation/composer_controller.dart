import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../domain/message.dart';

enum ComposerMode {
  idle,
  typing,
  replying,
  editing,
  recording,
  attachmentPreparing,
  sending,
}

class ComposerState {
  const ComposerState({
    this.mode = ComposerMode.idle,
    this.text = '',
    this.reply,
    this.editing,
    this.duration = Duration.zero,
    this.error,
  });
  final ComposerMode mode;
  final String text;
  final ChatMessage? reply, editing;
  final Duration duration;
  final String? error;
  ComposerState copyWith({
    ComposerMode? mode,
    String? text,
    ChatMessage? reply,
    ChatMessage? editing,
    Duration? duration,
    String? error,
    bool clearReply = false,
    bool clearEditing = false,
  }) => ComposerState(
    mode: mode ?? this.mode,
    text: text ?? this.text,
    reply: clearReply ? null : reply ?? this.reply,
    editing: clearEditing ? null : editing ?? this.editing,
    duration: duration ?? this.duration,
    error: error,
  );
}

class MessageComposerController extends Notifier<ComposerState> {
  @override
  ComposerState build() => const ComposerState();
  void setText(String value) {
    state = state.copyWith(
      text: value,
      mode: value.isEmpty
          ? ComposerMode.idle
          : state.reply != null
          ? ComposerMode.replying
          : state.editing != null
          ? ComposerMode.editing
          : ComposerMode.typing,
    );
  }

  void startReply(ChatMessage m) =>
      state = state.copyWith(mode: ComposerMode.replying, reply: m);
  void cancelReply() => state = state.copyWith(
    mode: state.text.isEmpty ? ComposerMode.idle : ComposerMode.typing,
    clearReply: true,
  );
  bool startEdit(ChatMessage m) {
    if (!m.isMine || m.type == MessageType.deleted) return false;
    state = state.copyWith(
      mode: ComposerMode.editing,
      text: m.text ?? '',
      editing: m,
    );
    return true;
  }

  void cancelEdit() => state = state.copyWith(
    mode: ComposerMode.idle,
    text: '',
    clearEditing: true,
  );
  bool saveEdit() => state.editing != null && state.text.trim().isNotEmpty;
  void startRecording() => state = state.copyWith(
    mode: ComposerMode.recording,
    duration: Duration.zero,
  );
  void cancelRecording() => state = state.copyWith(mode: ComposerMode.idle);
  void finishRecording() => state = state.copyWith(mode: ComposerMode.idle);
  void attachment() =>
      state = state.copyWith(mode: ComposerMode.attachmentPreparing);
}

final composerProvider =
    NotifierProvider<MessageComposerController, ComposerState>(
      MessageComposerController.new,
    );
