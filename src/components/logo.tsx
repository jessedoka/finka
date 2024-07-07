import Image from "next/image";

export default function Logo() {
    return (
        <div>
            <Image src='/favicon.svg' width={32} height={1} alt="" />
        </div>
    )
}

