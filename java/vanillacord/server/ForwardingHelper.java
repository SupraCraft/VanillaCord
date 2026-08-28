package vanillacord.server;

import com.google.common.collect.Multimap;
import com.mojang.authlib.GameProfile;
import com.mojang.authlib.properties.Property;
import com.mojang.authlib.properties.PropertyMap;

import java.lang.reflect.Constructor;
import java.lang.reflect.Method;
import java.util.UUID;

public abstract class ForwardingHelper {

    ForwardingHelper() {

    }

    public void parseHandshake(Object connection, Object handshake) {

    }

    public boolean initializeTransaction(Object connection, Object hello) {
        return false;
    }

    public boolean completeTransaction(Object connection, Object login, Object response) {
        return false;
    }

    public abstract GameProfile injectProfile(Object connection, String username);

    /**
     * Creates a GameProfile with the given properties pre-populated without
     * linking VanillaCord directly to one authlib API generation.
     *
     * Modern authlib exposes a three-argument GameProfile constructor carrying
     * a PropertyMap. Historical authlib instead exposes a two-argument
     * constructor plus a mutable getProperties() map. Both shapes are resolved
     * reflectively so compiling against the current Minecraft authlib does not
     * remove support for older server runtimes.
     */
    public static GameProfile createProfile(UUID id, String name, Multimap<String, Property> properties) {
        ReflectiveOperationException modernFailure;
        try {
            Constructor<PropertyMap> propertyMapConstructor = PropertyMap.class.getConstructor(Multimap.class);
            Constructor<GameProfile> profileConstructor = GameProfile.class.getConstructor(
                    UUID.class, String.class, PropertyMap.class);
            return profileConstructor.newInstance(id, name, propertyMapConstructor.newInstance(properties));
        } catch (ReflectiveOperationException e) {
            modernFailure = e;
        }

        try {
            Constructor<GameProfile> profileConstructor = GameProfile.class.getConstructor(UUID.class, String.class);
            GameProfile profile = profileConstructor.newInstance(id, name);
            Method getProperties = GameProfile.class.getMethod("getProperties");
            Object propertyMap = getProperties.invoke(profile);
            Method putAll = propertyMap.getClass().getMethod("putAll", Multimap.class);
            putAll.invoke(propertyMap, properties);
            return profile;
        } catch (ReflectiveOperationException historicalFailure) {
            modernFailure.addSuppressed(historicalFailure);
            throw new IllegalStateException("Unsupported authlib GameProfile API", modernFailure);
        }
    }
}
