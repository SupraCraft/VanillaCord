package vanillacord.server;

import com.mojang.authlib.properties.Property;
import io.netty.buffer.ByteBuf;
import io.netty.buffer.Unpooled;
import org.junit.jupiter.api.Test;

import javax.crypto.Mac;
import javax.crypto.spec.SecretKeySpec;
import java.lang.reflect.Method;
import java.util.List;
import java.util.UUID;

import static java.nio.charset.StandardCharsets.UTF_8;
import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertThrows;
import static org.junit.jupiter.api.Assertions.assertTrue;

class VelocityHelperTest {
    private static final String SECRET = "correct-horse-battery-staple";
    private static final UUID PLAYER_ID = UUID.fromString("12345678-1234-5678-9abc-def012345678");

    @Test
    void parsesValidForwardingPayload() throws Exception {
        VelocityForwardingParser parser = parserWith(SECRET);
        ByteBuf packet = forwardingPacket(SECRET, "203.0.113.42", PLAYER_ID, "TestPlayer");
        try {
            VelocityForwardingParser.ForwardedPlayerData parsed = parser.parse(packet);

            assertEquals("203.0.113.42", parsed.address());
            assertEquals(PLAYER_ID, parsed.playerId());
            assertEquals("TestPlayer", parsed.playerName());
            assertEquals(1, parsed.properties().size());
            assertTrue(parsed.properties().containsKey("textures"));

            Property property = parsed.properties().get("textures").iterator().next();
            assertEquals("texture-value", propertyComponent(property, "value"));
            assertEquals("texture-signature", propertyComponent(property, "signature"));
            assertEquals(0, packet.readableBytes());
        } finally {
            packet.release();
        }
    }

    @Test
    void rejectsPayloadSignedWithWrongSecret() throws Exception {
        VelocityForwardingParser parser = parserWith(SECRET);
        ByteBuf packet = forwardingPacket("wrong-secret", "203.0.113.42", PLAYER_ID, "TestPlayer");
        try {
            QuietException error = assertThrows(QuietException.class, () -> parser.parse(packet));
            assertEquals("Received invalid IP forwarding data. Did you use the right forwarding secret?", error.getMessage());
        } finally {
            packet.release();
        }
    }

    @Test
    void acceptsAnyConfiguredRotationSecret() throws Exception {
        VelocityForwardingParser parser = new VelocityForwardingParser(List.of("old-secret", "new-secret"));
        ByteBuf packet = forwardingPacket("new-secret", "198.51.100.17", PLAYER_ID, "RotatingPlayer");
        try {
            VelocityForwardingParser.ForwardedPlayerData parsed = parser.parse(packet);
            assertEquals("198.51.100.17", parsed.address());
            assertEquals("RotatingPlayer", parsed.playerName());
        } finally {
            packet.release();
        }
    }

    private static VelocityForwardingParser parserWith(String secret) {
        return new VelocityForwardingParser(List.of(secret));
    }

    private static ByteBuf forwardingPacket(String secret, String address, UUID id, String name) throws Exception {
        ByteBuf body = Unpooled.buffer();
        try {
            writeVarint(body, 1);
            writeString(body, address);
            body.writeLong(id.getMostSignificantBits());
            body.writeLong(id.getLeastSignificantBits());
            writeString(body, name);

            writeVarint(body, 1);
            writeString(body, "textures");
            writeString(body, "texture-value");
            body.writeBoolean(true);
            writeString(body, "texture-signature");

            byte[] raw = new byte[body.readableBytes()];
            body.getBytes(body.readerIndex(), raw);

            Mac mac = Mac.getInstance("HmacSHA256");
            mac.init(new SecretKeySpec(secret.getBytes(UTF_8), "HmacSHA256"));

            ByteBuf packet = Unpooled.buffer(32 + raw.length);
            packet.writeBytes(mac.doFinal(raw));
            packet.writeBytes(raw);
            return packet;
        } finally {
            body.release();
        }
    }

    private static void writeString(ByteBuf out, String value) {
        byte[] bytes = value.getBytes(UTF_8);
        writeVarint(out, bytes.length);
        out.writeBytes(bytes);
    }

    private static void writeVarint(ByteBuf out, int value) {
        int remaining = value;
        do {
            byte next = (byte) (remaining & 0x7F);
            remaining >>>= 7;
            if (remaining != 0) {
                next |= (byte) 0x80;
            }
            out.writeByte(next);
        } while (remaining != 0);
    }

    private static String propertyComponent(Property property, String component) throws Exception {
        for (String candidate : new String[] {component, "get" + Character.toUpperCase(component.charAt(0)) + component.substring(1)}) {
            try {
                Method method = Property.class.getMethod(candidate);
                Object value = method.invoke(property);
                return (value == null)? null : value.toString();
            } catch (NoSuchMethodException ignored) {
                // Support both record-style and legacy bean-style authlib APIs.
            }
        }
        throw new NoSuchMethodException("No authlib Property accessor for " + component);
    }
}
