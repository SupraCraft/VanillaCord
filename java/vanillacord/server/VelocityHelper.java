package vanillacord.server;

import bridge.Invocation;
import com.mojang.authlib.GameProfile;
import io.netty.buffer.ByteBuf;
import io.netty.buffer.EmptyByteBuf;
import io.netty.channel.Channel;
import io.netty.util.AttributeKey;
import vanillacord.translation.LoginExtension;
import vanillacord.translation.LoginListener;
import vanillacord.translation.NamespacedKey;
import vanillacord.translation.PlayerConnection;

import java.util.LinkedList;

@SuppressWarnings("SpellCheckingInspection")
public class VelocityHelper extends ForwardingHelper {
    private static final Object NAMESPACE = new Invocation(NamespacedKey.class).ofMethod("new").with("velocity").with("player_info").invoke();
    private static final AttributeKey<Object> LOGIN_KEY = AttributeKey.valueOf("-vch-login");
    private static final AttributeKey<GameProfile> PROFILE_KEY = AttributeKey.valueOf("-vch-profile");
    private final VelocityForwardingParser parser;

    VelocityHelper(LinkedList<String> seecrets) {
        parser = new VelocityForwardingParser(seecrets);
    }

    public boolean initializeTransaction(Object connection, Object intercepted) {
        try {
            Channel channel = new Invocation(PlayerConnection.class).ofMethod("getChannel").with(connection).invoke();
            if (channel.attr(LOGIN_KEY).get() != null)
                throw new IllegalStateException("Unexpected login request");
            if (channel.attr(PROFILE_KEY).get() != null) {
                return false;
            }

            channel.attr(LOGIN_KEY).set(intercepted);
            new Invocation(LoginExtension.class).ofMethod("send")
                    .with(connection)
                    .with(0)
                    .with(NAMESPACE)
                    .with(ByteBuf.class, new EmptyByteBuf(channel.alloc()))
                    .invoke();

        } catch (Exception e) {
            throw QuietException.show(e);
        }
        return true;
    }

    public boolean completeTransaction(Object connection, Object login, Object response) {
        try {
            Channel channel = new Invocation(PlayerConnection.class).ofMethod("getChannel").with(connection).invoke();
            Object intercepted = channel.attr(LOGIN_KEY).get();
            if (intercepted == null) {
                return false;
            }

            int id = new Invocation(LoginExtension.class).ofMethod("getTransactionID").with(response).invoke();
            ByteBuf data = new Invocation(LoginExtension.class).ofMethod("getData").with(response).invoke();

            if (id != 0)
                throw QuietException.notify("Unknown transaction ID: " + id);
            if (data == null)
                throw QuietException.notify("If you wish to use modern IP forwarding, please enable it in your Velocity config as well!");

            VelocityForwardingParser.ForwardedPlayerData forwarded = parser.parse(data);
            new Invocation(PlayerConnection.class).ofMethod("setAddress").with(connection).with(forwarded.address()).invoke();
            GameProfile profile = ForwardingHelper.createProfile(
                    forwarded.playerId(), forwarded.playerName(), forwarded.properties());
            channel.attr(PROFILE_KEY).set(profile);

            try {
                new Invocation(LoginListener.class).ofMethod("hello")
                        .with(login)
                        .with(intercepted)
                        .invoke();

            } finally {
                channel.attr(LOGIN_KEY).set(null);
            }
        } catch (Exception e) {
            throw QuietException.show(e);
        }
        return true;
    }

    @Override
    public GameProfile injectProfile(Object connection, String username) {
        try {
            return ((Channel) new Invocation(PlayerConnection.class).ofMethod("getChannel").with(connection).invoke()).attr(PROFILE_KEY).get();
        } catch (Exception e) {
            throw QuietException.show(e);
        }
    }
}
