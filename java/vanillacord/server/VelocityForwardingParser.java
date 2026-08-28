package vanillacord.server;

import com.google.common.collect.ArrayListMultimap;
import com.google.common.collect.Multimap;
import com.mojang.authlib.properties.Property;
import io.netty.buffer.ByteBuf;

import javax.crypto.Mac;
import javax.crypto.spec.SecretKeySpec;
import java.security.InvalidKeyException;
import java.security.NoSuchAlgorithmException;
import java.util.Arrays;
import java.util.Iterator;
import java.util.UUID;

import static java.nio.charset.StandardCharsets.UTF_8;

final class VelocityForwardingParser {
    private final byte[][] secrets;

    VelocityForwardingParser(Iterable<String> secrets) {
        int length = 0;
        for (String ignored : secrets) {
            ++length;
        }

        byte[][] array = this.secrets = new byte[length][];
        int i = 0;
        for (String secret : secrets) {
            array[i++] = secret.getBytes(UTF_8);
        }
    }

    ForwardedPlayerData parse(ByteBuf data) throws NoSuchAlgorithmException, InvalidKeyException {
        if (invalidSignature(data)) {
            throw QuietException.notify("Received invalid IP forwarding data. Did you use the right forwarding secret?");
        }

        readVarint(data); // forwarding protocol version; currently no branching is required
        String address = readString(data);
        UUID playerId = new UUID(data.readLong(), data.readLong());
        String playerName = readString(data);
        Multimap<String, Property> properties = ArrayListMultimap.create();
        for (int i = 0, length = readVarint(data); i < length; ++i) {
            String propertyName = readString(data);
            properties.put(propertyName, new Property(
                    propertyName,
                    readString(data),
                    data.readBoolean() ? readString(data) : null));
        }

        return new ForwardedPlayerData(address, playerId, playerName, properties);
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

    record ForwardedPlayerData(
            String address,
            UUID playerId,
            String playerName,
            Multimap<String, Property> properties) {
    }
}
