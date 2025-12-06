# TikTokLive Events Reference

This document provides a comprehensive list of all available events in the TikTokLive library, organized by category.

## Table of Contents
- [Custom Events](#custom-events)
- [Core Stream Events](#core-stream-events)
- [User Interaction Events](#user-interaction-events)
- [Gift & Monetization Events](#gift--monetization-events)
- [Live Stream Management Events](#live-stream-management-events)
- [Gaming & Interactive Events](#gaming--interactive-events)
- [Moderation & Control Events](#moderation--control-events)
- [Technical & System Events](#technical--system-events)
- [Commerce & Shopping Events](#commerce--shopping-events)
- [Advanced Features Events](#advanced-features-events)

---

## Custom Events

These are high-level events provided by TikTokLive for common use cases.

| Event Name | Description | Use Case | Key Properties |
|------------|-------------|----------|----------------|
| `ConnectEvent` | Triggered when successfully connected to a live stream | Connection handling, initialization | `unique_id`, `room_id` |
| `DisconnectEvent` | Triggered when disconnected from a live stream | Cleanup, reconnection logic | - |
| `LiveEndEvent` | Triggered when the live stream ends | Stream monitoring, cleanup | Inherits from `ControlEvent` |
| `LivePauseEvent` | Triggered when the stream is paused | Stream state tracking | Inherits from `ControlEvent` |
| `LiveUnpauseEvent` | Triggered when a paused stream resumes | Stream state tracking | Inherits from `ControlEvent` |
| `FollowEvent` | Triggered when someone follows the streamer | Social engagement tracking | Inherits from `SocialEvent` |
| `ShareEvent` | Triggered when someone shares the stream | Viral tracking, analytics | `users_joined` property |
| `SuperFanEvent` | Triggered for super fan interactions | VIP user tracking | Inherits from `BarrageEvent` |
| `WebsocketResponseEvent` | Triggered for any WebSocket message | Low-level debugging | Raw message data |
| `UnknownEvent` | Triggered for unrecognized messages | Future-proofing, debugging | Raw message data |

---

## Core Stream Events

Essential events for basic live stream functionality.

| Event Name | Description | Use Case | Key Properties |
|------------|-------------|----------|----------------|
| `CommentEvent` | User posts a comment in chat | Chat moderation, interaction | `user`, `content`, `comment` |
| `JoinEvent` | User joins the live stream | Welcome messages, analytics | `user`, `operator` |
| `LikeEvent` | User likes the stream | Engagement tracking | `user`, `count` |
| `DiggEvent` | User "digs" (likes) content | Engagement metrics | `user` |
| `RoomUserSeqEvent` | Viewer count updates | Real-time analytics | `m_total`, `m_contributors` |
| `SocialEvent` | General social interactions | Base class for social events | `user`, `display_text` |
| `ControlEvent` | Stream control messages | Stream state management | `action` |

---

## User Interaction Events

Events related to user participation and engagement.

| Event Name | Description | Use Case | Key Properties |
|------------|-------------|----------|----------------|
| `EmoteChatEvent` | User sends emote in chat | Enhanced chat experience | `user` |
| `MessageDetectEvent` | Message content detection | Content moderation | Message analysis |
| `CommentTrayEvent` | Comment tray interactions | UI state management | Comment data |
| `CommentsEvent` | Batch comment events | Bulk comment processing | `user` |
| `HashtagEvent` | Hashtag-related events | Trend tracking | Hashtag data |
| `ScreenChatEvent` | Screen chat interactions | Interactive features | `user_info` |
| `StarCommentPushEvent` | Highlighted comment events | VIP comment handling | Comment data |
| `StarCommentNotificationEvent` | Star comment notifications | Notification system | Comment data |

---

## Gift & Monetization Events

Events related to virtual gifts and monetization.

| Event Name | Description | Use Case | Key Properties |
|------------|-------------|----------|----------------|
| `GiftEvent` | User sends a virtual gift | Revenue tracking, thank you messages | `gift`, `user`, `repeat_count` |
| `GiftBroadcastEvent` | Gift broadcast messages | Public gift announcements | Gift data |
| `GiftCollectionUpdateEvent` | Gift collection changes | Gift inventory management | Collection data |
| `GiftDynamicRestrictionEvent` | Gift restriction updates | Gift policy enforcement | Restriction data |
| `GiftGalleryEvent` | Gift gallery interactions | Gift browsing | Gallery data |
| `GiftGuideEvent` | Gift guide interactions | User education | Guide data |
| `GiftNoticeEvent` | Gift notification events | Gift alerts | Notice data |
| `GiftPanelUpdateEvent` | Gift panel UI updates | Interface management | Panel data |
| `GiftProgressEvent` | Gift progress tracking | Achievement system | Progress data |
| `GiftPromptEvent` | Gift prompting events | Monetization optimization | Prompt data |
| `GiftRecordCapsuleEvent` | Gift record capsules | Gift history | Record data |
| `GiftUnlockEvent` | Gift unlock events | Feature unlocking | Unlock data |
| `GiftUpdateEvent` | Gift system updates | Gift management | Update data |
| `EnvelopeEvent` | Red envelope events | Special gift events | Envelope data |
| `EnvelopePortalEvent` | Envelope portal interactions | Envelope UI | Portal data |

---

## Live Stream Management Events

Events for managing live stream settings and features.

| Event Name | Description | Use Case | Key Properties |
|------------|-------------|----------|----------------|
| `RoomEvent` | General room events | Room state management | Room data |
| `RoomEventEvent` | Specific room event triggers | Event handling | Event data |
| `RoomNotifyEvent` | Room notifications | Alert system | Notification data |
| `RoomVerifyEvent` | Room verification events | Security, validation | Verification data |
| `RoomBottomEvent` | Bottom panel events | UI management | Panel data |
| `RoomPinEvent` | Room pinning events | Content highlighting | Pin data |
| `RoomStickerEvent` | Room sticker events | Visual enhancements | Sticker data |
| `RoomStreamAdaptationEvent` | Stream quality adaptation | Performance optimization | Adaptation data |
| `StreamStatusEvent` | Stream status changes | Status monitoring | Status data |
| `ColdStartEvent` | Stream cold start events | Performance monitoring | Start data |
| `HotRoomEvent` | Hot room notifications | Trending detection | Room data |

---

## Gaming & Interactive Events

Events related to gaming features and interactive content.

| Event Name | Description | Use Case | Key Properties |
|------------|-------------|----------|----------------|
| `GameEmoteUpdateEvent` | Game emote updates | Gaming integration | Emote data |
| `GameGuessToastEvent` | Game guess notifications | Interactive games | Guess data |
| `GameGuessPinCardEvent` | Game guess pin cards | Game UI | Card data |
| `GameGuessWidgetsEvent` | Game guess widgets | Interactive widgets | Widget data |
| `GameMomentEvent` | Game moment captures | Highlight system | Moment data |
| `GameOcrPingEvent` | Game OCR ping events | Text recognition | OCR data |
| `GameRankNotifyEvent` | Game ranking notifications | Leaderboards | Rank data |
| `GameRecommendCreateGuessEvent` | Game recommendation events | AI suggestions | Recommendation data |
| `GameReqSetGuessEvent` | Game guess requests | Interactive gaming | Request data |
| `GameServerFeatureEvent` | Game server features | Server management | Feature data |
| `GameSettingChangeEvent` | Game setting changes | Configuration | Settings data |
| `PictionaryStartEvent` | Pictionary game start | Drawing games | Game data |
| `PictionaryUpdateEvent` | Pictionary game updates | Game progress | Update data |
| `PictionaryEndEvent` | Pictionary game end | Game completion | End data |
| `PictionaryExitEvent` | Pictionary game exit | Game termination | Exit data |
| `PlayTogetherEvent` | Play together events | Multiplayer features | Play data |
| `PlaybookEvent` | Playbook events | Game strategy | Playbook data |

---

## Moderation & Control Events

Events for content moderation and stream control.

| Event Name | Description | Use Case | Key Properties |
|------------|-------------|----------|----------------|
| `AccessControlEvent` | Access control changes | Permission management | Control data |
| `AccessRecallEvent` | Access recall events | Permission revocation | Recall data |
| `AuthorizationNotifyEvent` | Authorization notifications | Security alerts | Auth data |
| `UnauthorizedMemberEvent` | Unauthorized member detection | Security monitoring | Member data |
| `ImDeleteEvent` | Message deletion events | Content moderation | Delete data |
| `MgPunishCenterActionEvent` | Punishment center actions | Moderation actions | Action data |
| `PartnershipPunishEvent` | Partnership punishment | Business moderation | Punishment data |
| `BizStickerEvent` | Business sticker events | Commercial content | Sticker data |
| `NoticeEvent` | General notice events | Announcements | Notice data |
| `NoticeboardEvent` | Noticeboard updates | Information display | Board data |
| `NoticeboardReviewEvent` | Noticeboard review events | Content review | Review data |

---

## Technical & System Events

Low-level technical and system events.

| Event Name | Description | Use Case | Key Properties |
|------------|-------------|----------|----------------|
| `EffectControlEvent` | Visual effect controls | Effect management | Effect data |
| `EffectPreloadingEvent` | Effect preloading events | Performance optimization | Preload data |
| `InteractiveEffectEvent` | Interactive effect events | User interactions | Effect data |
| `CaptionEvent` | Caption/subtitle events | Accessibility features | Caption data |
| `CountdownEvent` | Countdown timer events | Time-based features | Timer data |
| `CountdownForAllEvent` | Global countdown events | Synchronized timers | Timer data |
| `PerceptionEvent` | Perception system events | AI/ML features | Perception data |
| `AiSummaryEvent` | AI summary generation | Content summarization | Summary data |
| `AiLiveSummaryEvent` | AI live summary events | Real-time AI | Summary data |
| `RealTimePerformancePageEvent` | Performance monitoring | Analytics | Performance data |
| `RealtimeLiveCenterMethodEvent` | Live center methods | System integration | Method data |

---

## Commerce & Shopping Events

Events related to e-commerce and shopping features.

| Event Name | Description | Use Case | Key Properties |
|------------|-------------|----------|----------------|
| `VideoLiveGoodsRcmdEvent` | Product recommendations | Shopping integration | Product data |
| `VideoLiveGoodsOrderEvent` | Product order events | E-commerce tracking | Order data |
| `PaidContentLiveShoppingEvent` | Paid shopping content | Premium shopping | Content data |
| `EcBarrageEvent` | E-commerce barrage events | Shopping promotions | Barrage data |
| `EcDrawEvent` | E-commerce draw events | Shopping games | Draw data |
| `EcTaskRefreshCouponListEvent` | Coupon list refresh | Discount management | Coupon data |
| `CommercialCustomEvent` | Custom commercial events | Business integration | Commercial data |
| `BaLeadGenEvent` | Lead generation events | Business development | Lead data |
| `PartnershipDropsCardChangeEvent` | Partnership drops changes | Collaboration features | Drop data |
| `PartnershipDropsUpdateEvent` | Partnership drops updates | Partnership management | Update data |
| `PartnershipDropsAnchorEvent` | Partnership anchor events | Anchor partnerships | Anchor data |

---

## Advanced Features Events

Events for advanced and specialized features.

| Event Name | Description | Use Case | Key Properties |
|------------|-------------|----------|----------------|
| `LinkMicBattleEvent` | Link mic battle events | Multi-user features | Battle data |
| `LinkMicArmiesEvent` | Link mic armies | Group interactions | Army data |
| `LinkMicMethodEvent` | Link mic methods | Connection management | Method data |
| `LinkMicSignalingMethodEvent` | Link mic signaling | Communication protocol | Signal data |
| `LinkMicAnchorGuideEvent` | Link mic anchor guide | User guidance | Guide data |
| `LinkMicAdEvent` | Link mic advertisement | Monetization | Ad data |
| `LinkMicFanTicketMethodEvent` | Fan ticket methods | VIP features | Ticket data |
| `LinkmicAnimationEvent` | Link mic animations | Visual effects | Animation data |
| `LinkmicAudienceNoticeEvent` | Audience notice events | Communication | Notice data |
| `LinkmicBattleNoticeEvent` | Battle notice events | Competition alerts | Notice data |
| `LinkmicBattleTaskEvent` | Battle task events | Task management | Task data |
| `SubNotifyEvent` | Subscription notifications | Subscriber management | Sub data |
| `SubQueueEvent` | Subscription queue events | Queue management | Queue data |
| `SubTimerStickerEvent` | Subscription timer stickers | Visual indicators | Sticker data |
| `SubWaveEvent` | Subscription wave events | Subscriber celebrations | Wave data |
| `SubPinEventEvent` | Subscription pin events | Subscriber highlights | Pin data |
| `SubContractStatusEvent` | Subscription contract status | Business management | Contract data |

---

## Usage Examples

### Basic Event Handling
```python
from TikTokLive import TikTokLiveClient
from TikTokLive.events import ConnectEvent, CommentEvent, GiftEvent, JoinEvent

client = TikTokLiveClient(unique_id="username")

@client.on(ConnectEvent)
async def on_connect(event: ConnectEvent):
    print(f"Connected to @{event.unique_id}")

@client.on(CommentEvent)
async def on_comment(event: CommentEvent):
    print(f"{event.user.nickname}: {event.comment}")

@client.on(GiftEvent)
async def on_gift(event: GiftEvent):
    print(f"{event.user.nickname} sent {event.gift.name}")

@client.on(JoinEvent)
async def on_join(event: JoinEvent):
    print(f"{event.user.nickname} joined!")

client.run()
```

### Advanced Event Handling
```python
from TikTokLive.events import RoomUserSeqEvent, LiveEndEvent, FollowEvent

@client.on(RoomUserSeqEvent)
async def on_viewer_update(event: RoomUserSeqEvent):
    print(f"👥 Viewers: {event.m_total}")

@client.on(LiveEndEvent)
async def on_live_end(event: LiveEndEvent):
    print("🔴 Stream ended!")

@client.on(FollowEvent)
async def on_follow(event: FollowEvent):
    print(f"➕ New follower: {event.user.nickname}")
```

---

## Notes

- **Event Inheritance**: Many events inherit from base classes like `BaseEvent`, `SocialEvent`, `ControlEvent`, etc.
- **User Properties**: Most user interaction events include a `user` property with user information
- **Extensibility**: The `UnknownEvent` catches unrecognized messages for future compatibility
- **Performance**: Use specific events rather than `WebsocketResponseEvent` for better performance
- **Documentation**: Some events may have additional properties not listed here - check the source code for complete details

---

*This documentation is based on TikTokLive library version 6.6.5*
