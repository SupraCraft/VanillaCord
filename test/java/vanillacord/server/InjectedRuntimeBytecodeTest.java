package vanillacord.server;

import org.junit.jupiter.api.Test;
import org.objectweb.asm.ClassReader;
import org.objectweb.asm.ClassVisitor;
import org.objectweb.asm.MethodVisitor;
import org.objectweb.asm.Opcodes;

import java.io.DataInputStream;
import java.io.InputStream;
import java.util.ArrayList;
import java.util.List;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertNotNull;
import static org.junit.jupiter.api.Assertions.assertTrue;

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

    @Test
    void bungeeHelperDoesNotDirectlyLinkModernOnlyRuntimeApis() throws Exception {
        String resource = "vanillacord/server/BungeeHelper.class";
        ClassLoader loader = Thread.currentThread().getContextClassLoader();
        List<String> forbiddenLinks = new ArrayList<>();

        try (InputStream raw = loader.getResourceAsStream(resource)) {
            assertNotNull(raw, () -> "missing injected runtime class: " + resource);
            new ClassReader(raw).accept(new ClassVisitor(Opcodes.ASM9) {
                @Override
                public MethodVisitor visitMethod(int access, String name, String descriptor, String signature, String[] exceptions) {
                    return new MethodVisitor(Opcodes.ASM9) {
                        @Override
                        public void visitMethodInsn(int opcode, String owner, String methodName, String methodDescriptor, boolean isInterface) {
                            boolean modernPropertyAccessor = owner.equals("com/mojang/authlib/properties/Property")
                                    && (methodName.equals("name") || methodName.equals("value") || methodName.equals("signature"));
                            boolean modernAttributeKeyFactory = owner.equals("io/netty/util/AttributeKey")
                                    && methodName.equals("valueOf")
                                    && methodDescriptor.equals("(Ljava/lang/String;)Lio/netty/util/AttributeKey;");
                            if (modernPropertyAccessor || modernAttributeKeyFactory) {
                                forbiddenLinks.add(owner + "." + methodName + methodDescriptor);
                            }
                        }
                    };
                }
            }, ClassReader.SKIP_DEBUG | ClassReader.SKIP_FRAMES);
        }

        assertTrue(
                forbiddenLinks.isEmpty(),
                () -> "BungeeHelper spans the oldest supported Minecraft generations and must not directly link APIs absent from historical authlib/Netty runtimes: " + forbiddenLinks
        );
    }
}
