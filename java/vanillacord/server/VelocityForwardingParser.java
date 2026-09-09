package vanillacord.server;

import io.netty.buffer.ByteBuf;

import javax.crypto.Mac;
import javax.crypto.spec.SecretKeySpec;
import java.security.InvalidKeyException;
import java.security.NoSuchAlgorithmException;
import java.util.ArrayList;
import java.util.Arrays;
import java.util.Collections;
import java.util.List;
import java.util.UUID;

import static java.nio.charset.StandardCharsets.UTF_8;

final class VelocityForwardingParser {
    private final byte[][] secrets;

    VelocityForwardingParser(Iterable<String> secrets) {
        List<byte[]> encoded = new ArrayList<>();
        for (String secret : secrets) {
            encoded.add(secret.getBytes(UTF_8));
        }
        this.secrets = encoded.toArray(new byte[encoded.size()][]);
    }

    ForwardedPlayerData parse(ByteBuf data) throws NoSuchAlgorithmException, InvalidKeyException {
        if (invalidSignature(data)) {
            throw QuietException.notify("Received invalid IP forwarding data. Did you use the right forwarding secret?");
        }

        readVarint(data); // forwarding protocol version; currently no branching is required
        String address = readString(data);
        UUID playerId = new UUID(data.readLong(), data.readLong());
        String playerName = readString(data);
        List<ForwardedProperty> properties = new ArrayList<>();
        for (int i = 0, length = readVarint(data); i < length; ++i) {
            String propertyName = readString(data);
            String propertyValue = readString(data);
            String propertySignature = data.readBoolean() ? readString(data) : null;
            properties.add(new ForwardedProperty(propertyName, propertyValue, propertySignature));
        }

        return new ForwardedPlayerData(
                address,
                playerId,
                playerName,
                Collections.unmodifiableList(new ArrayList<>(properties))
        );
    }

    private boolean invalidSignature(ByteBuf data) throws NoSuchAlgorithmException, InvalidKeyException {
        byte[] signature = new byte[32];
        data.readBytes(signature);

        byte[] raw = new byte[data.readableBytes()];
        data.readBytes(raw).readerIndex(signature.length);

        Mac mac = Mac.getInstance("HmacSHA256");
        for (byte[] secret : secrets) {
            mac.init(new SecretKeySpec(secret, "HmacSHA256"));
            mac.update(raw);
            if (Arrays.equals(signature, mac.doFinal())) {
                return false;
            }
        }
        return true;
    }

    private static String readString(ByteBuf buf) {
        int len = readVarint(buf);
        if (len > Short.MAX_VALUE * 3) {
            throw new RuntimeException("String is too long");
        }

        String value = buf.toString(buf.readerIndex(), len, UTF_8);
        buf.readerIndex(buf.readerIndex() + len);
        if (value.length() > Short.MAX_VALUE) {
            throw new RuntimeException("String is too long");
        }
        return value;
    }

    private static int readVarint(ByteBuf input) {
        int out = 0;
        int bytes = 0;
        byte in;
        do {
            in = input.readByte();
            out |= (in & 0x7F) << (bytes++ * 7);
            if (bytes > 5) {
                throw new RuntimeException("Varint is too big");
            }
        } while ((in & 0x80) == 0x80);
        return out;
    }

    static final class ForwardedProperty {
        private final String name;
        private final String value;
        private final String signature;

        ForwardedProperty(String name, String value, String signature) {
            this.name = name;
            this.value = value;
            this.signature = signature;
        }

        String name() {
            return name;
        }

        String value() {
            return value;
        }

        String signature() {
            return signature;
        }
    }

    static final class ForwardedPlayerData {
        private final String address;
        private final UUID playerId;
        private final String playerName;
        private final List<ForwardedProperty> properties;

        ForwardedPlayerData(String address, UUID playerId, String playerName, List<ForwardedProperty> properties) {
            this.address = address;
            this.playerId = playerId;
            this.playerName = playerName;
            this.properties = properties;
        }

        String address() {
            return address;
        }

        UUID playerId() {
            return playerId;
        }

        String playerName() {
            return playerName;
        }

        List<ForwardedProperty> properties() {
            return properties;
        }
    }
}
