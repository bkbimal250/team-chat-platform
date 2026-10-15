# Folder structure

```
lib/
  app/                 # MaterialApp, router
  config/              # dart-define configuration
  theme/               # GcTheme + tokens
  components/          # Shared UI & layout shell
  features/
    auth/
    chats/
    contacts/
    notifications/     # Updates tab
    workspace/
    settings/
    groups/              # existing group flows
    messages/            # existing message UI pieces
  services/            # api, realtime, storage (phased)
  core/                # firebase, notifications (existing)
```

Legacy top-level feature files (`login_screen.dart`, `chat_screen.dart`) remain until migrated; new work goes under `features/<name>/`.
