declare namespace Telegram {
  interface ThemeParams {
    bg_color?: string
    text_color?: string
    hint_color?: string
    link_color?: string
    button_color?: string
    button_text_color?: string
    secondary_bg_color?: string
    header_bg_color?: string
    bottom_bar_bg_color?: string
    accent_text_color?: string
    section_bg_color?: string
    section_header_text_color?: string
    section_separator_color?: string
    subtitle_text_color?: string
    destructive_text_color?: string
  }

  interface WebAppUser {
    id: number
    is_bot?: boolean
    first_name: string
    last_name?: string
    username?: string
    language_code?: string
    is_premium?: true
    added_to_attachment_menu?: true
    allows_write_to_pm?: true
    photo_url?: string
  }

  interface WebAppChat {
    id: number
    type: 'group' | 'supergroup' | 'channel'
    title: string
    username?: string
    photo_url?: string
  }

  interface WebAppInitData {
    query_id?: string
    user?: WebAppUser
    receiver?: WebAppUser
    chat?: WebAppChat
    chat_type?: 'sender' | 'private' | 'group' | 'supergroup' | 'channel'
    chat_instance?: string
    start_param?: string
    can_send_after?: number
    auth_date: number
    hash: string
    signature?: string
  }

  interface SafeAreaInset {
    top: number
    bottom: number
    left: number
    right: number
  }

  interface ContentSafeAreaInset {
    top: number
    bottom: number
    left: number
    right: number
  }

  interface BackButton {
    isVisible: boolean
    onClick(callback: () => void): BackButton
    offClick(callback: () => void): BackButton
    show(): BackButton
    hide(): BackButton
  }

  interface BottomButton {
    type: 'main' | 'secondary'
    iconCustomEmojiId?: string
    text: string
    color: string
    textColor: string
    isVisible: boolean
    isActive: boolean
    hasShineEffect?: boolean
    position?: 'left' | 'right' | 'top' | 'bottom'
    isProgressVisible: boolean
    setText(text: string): BottomButton
    onClick(callback: () => void): BottomButton
    offClick(callback: () => void): BottomButton
    show(): BottomButton
    hide(): BottomButton
    enable(): BottomButton
    disable(): BottomButton
    showProgress(leaveActive?: boolean): BottomButton
    hideProgress(): BottomButton
    setParams(params: Record<string, unknown>): BottomButton
  }

  interface SettingsButton {
    isVisible: boolean
    onClick(callback: () => void): SettingsButton
    offClick(callback: () => void): SettingsButton
    show(): SettingsButton
    hide(): SettingsButton
  }

  interface HapticFeedback {
    impactOccurred(style: 'light' | 'medium' | 'heavy' | 'rigid' | 'soft'): HapticFeedback
    notificationOccurred(type: 'error' | 'success' | 'warning'): HapticFeedback
    selectionChanged(): HapticFeedback
  }

  type CloudStorageCallback = (error: Error | null, result?: unknown) => void

  interface CloudStorage {
    setItem(key: string, value: string, callback?: CloudStorageCallback): CloudStorage
    getItem(key: string, callback: CloudStorageCallback): CloudStorage
    getItems(keys: string[], callback: CloudStorageCallback): CloudStorage
    removeItem(key: string, callback?: CloudStorageCallback): CloudStorage
    removeItems(keys: string[], callback?: CloudStorageCallback): CloudStorage
    getKeys(callback: CloudStorageCallback): CloudStorage
  }

  /** События `WebApp.onEvent` — см. таблицу в документации Telegram Mini Apps */
  type WebAppEventType =
    | 'activated'
    | 'deactivated'
    | 'themeChanged'
    | 'viewportChanged'
    | 'safeAreaChanged'
    | 'contentSafeAreaChanged'
    | 'mainButtonClicked'
    | 'secondaryButtonClicked'
    | 'backButtonClicked'
    | 'settingsButtonClicked'
    | 'invoiceClosed'
    | 'popupClosed'
    | 'qrTextReceived'
    | 'scanQrPopupClosed'
    | 'clipboardTextReceived'
    | 'writeAccessRequested'
    | 'contactRequested'
    | 'biometricManagerUpdated'
    | 'biometricAuthRequested'
    | 'biometricTokenUpdated'
    | 'fullscreenChanged'
    | 'fullscreenFailed'
    | 'homeScreenAdded'
    | 'homeScreenChecked'
    | 'accelerometerStarted'
    | 'accelerometerStopped'
    | 'accelerometerChanged'
    | 'accelerometerFailed'
    | 'deviceOrientationStarted'
    | 'deviceOrientationStopped'
    | 'deviceOrientationChanged'
    | 'deviceOrientationFailed'
    | 'gyroscopeStarted'
    | 'gyroscopeStopped'
    | 'gyroscopeChanged'
    | 'gyroscopeFailed'
    | 'locationManagerUpdated'
    | 'locationRequested'
    | 'shareMessageSent'
    | 'shareMessageFailed'
    | 'emojiStatusSet'
    | 'emojiStatusFailed'
    | 'emojiStatusAccessRequested'
    | 'fileDownloadRequested'

  interface WebApp {
    initData: string
    initDataUnsafe: WebAppInitData
    version: string
    platform: string
    colorScheme: 'light' | 'dark'
    themeParams: ThemeParams
    isActive?: boolean
    isExpanded: boolean
    viewportHeight: number
    viewportStableHeight: number
    headerColor: string
    backgroundColor: string
    bottomBarColor: string
    isClosingConfirmationEnabled: boolean
    isVerticalSwipesEnabled: boolean
    isFullscreen?: boolean
    isOrientationLocked?: boolean
    safeAreaInset?: SafeAreaInset
    contentSafeAreaInset?: ContentSafeAreaInset
    BackButton: BackButton
    MainButton: BottomButton
    SecondaryButton: BottomButton
    SettingsButton: SettingsButton
    HapticFeedback: HapticFeedback
    CloudStorage: CloudStorage
    BiometricManager: Record<string, unknown>
    Accelerometer?: Record<string, unknown>
    DeviceOrientation?: Record<string, unknown>
    Gyroscope?: Record<string, unknown>
    LocationManager?: Record<string, unknown>
    DeviceStorage?: Record<string, unknown>
    SecureStorage?: Record<string, unknown>

    isVersionAtLeast(version: string): boolean
    setHeaderColor(color: string): void
    setBackgroundColor(color: string): void
    setBottomBarColor(color: string): void
    enableClosingConfirmation(): void
    disableClosingConfirmation(): void
    enableVerticalSwipes(): void
    disableVerticalSwipes(): void
    requestFullscreen(): void
    exitFullscreen(): void
    lockOrientation(): void
    unlockOrientation(): void
    addToHomeScreen(): void
    checkHomeScreenStatus(callback?: (status: string) => void): void
    /** В обработчике `this` — текущий `WebApp`; набор аргументов зависит от `eventType` (см. документацию). */
    onEvent(eventType: WebAppEventType, eventHandler: (...args: unknown[]) => void): void
    offEvent(eventType: WebAppEventType, eventHandler: (...args: unknown[]) => void): void
    sendData(data: string): void
    switchInlineQuery(query: string, choose_chat_types?: string[]): void
    openLink(url: string, options?: { try_instant_view?: boolean }): void
    openTelegramLink(url: string): void
    openInvoice(url: string, callback?: (status: string) => void): void
    shareToStory(media_url: string, params?: Record<string, unknown>): void
    shareMessage(msg_id: string, callback?: (success: boolean) => void): void
    setEmojiStatus(
      custom_emoji_id: string,
      params?: Record<string, unknown>,
      callback?: (success: boolean) => void,
    ): void
    requestEmojiStatusAccess(callback?: (granted: boolean) => void): void
    downloadFile(params: { url: string; file_name: string }, callback?: (accepted: boolean) => void): void
    hideKeyboard(): void
    showPopup(
      params: { title?: string; message: string; buttons?: unknown[] },
      callback?: (buttonId: string | null) => void,
    ): void
    showAlert(message: string, callback?: () => void): void
    showConfirm(message: string, callback?: (ok: boolean) => void): void
    showScanQrPopup(params: { text?: string }, callback?: (data: string) => boolean | void): void
    closeScanQrPopup(): void
    readTextFromClipboard(callback?: (text: string | null) => void): void
    requestWriteAccess(callback?: (allowed: boolean) => void): void
    requestContact(callback?: (sent: boolean) => void): void
    requestChat(req_id: string, callback?: (success: boolean) => void): void
    ready(): void
    expand(): void
    close(): void
  }
}

declare global {
  interface Window {
    Telegram?: {
      WebApp: Telegram.WebApp
    }
  }
}

export {}
