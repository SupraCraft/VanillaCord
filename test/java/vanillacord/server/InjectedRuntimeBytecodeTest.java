package vanillacord.server;

import org.junit.jupiter.api.Test;

import java.io.DataInputStream;
import java.io.InputStream;
import java.util.List;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertNotNull;

class InjectedRuntimeBytecodeTest {
    private static final int JAVA_8_CLASS_MAJOR = 52;

    private static final List<String> INJECTED_SERVER_CLASSES = List.of(
            "vanillacord/server/VanillaCord.class",
            "vanillacord/server/QuietException.class",
            "vanillacord/server/ForwardingHelper.class",
            "vanillacord/server/BungeeHelper.class",
            "vanillacord/server/VelocityHelper.class",
            "vanillacord/server/VelocityForwardingParser.class",
            "vanillacord/server/VelocityForwardingParser$ForwardedProperty.class",
            "vanillacord/server/VelocityForwardingParser$ForwardedPlayerData.class"
    );

    @Test
    void injectedServerClassesRemainJava8Compatible() throws Exception {
        ClassLoader loader = Thread.currentThread().getContextClassLoader();
        for (String resource : INJECTED_SERVER_CLASSES) {
            try (InputStream raw = loader.getResourceAsStream(resource)) {
                assertNotNull(raw, () -> "missing injected runtime class: " + resource);
                try (DataInputStream in = new DataInputStream(raw)) {
                    assertEquals(0xCAFEBABE, in.readInt(), () -> "invalid classfile: " + resource);
                    in.readUnsignedShort(); // minor version
                    int major = in.readUnsignedShort();
                    assertEquals(
                            JAVA_8_CLASS_MAJOR,
                            major,
                            () -> resource + " must remain Java 8 bytecode because supported Minecraft includes Java 8 runtimes"
                    );
                }
            }
        }
    }
}
